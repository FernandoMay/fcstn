"""Real EEG acquisition module - Muse BLE, OpenBCI Serial, and recorded data."""

import struct
import time
import logging
import threading
import numpy as np
from collections import deque

log = logging.getLogger('BCI.Acq')

# Channel names for Muse 2/S
MUSE_CHANNELS = ['TP9', 'AF7', 'AF8', 'TP10']
# Channel names for OpenBCI (8 or 16 channels)
OBCI_CHANNELS_8 = [f'Ch{i}' for i in range(1, 9)]
OBCI_CHANNELS_16 = [f'Ch{i}' for i in range(1, 17)]

# Muse BLE UUIDs
MUSE_SERVICE = 'FE8D'
MUSE_EEG_CHAR = '273e0003-4c4d-454d-96be-f03bac821358'
MUSE_CTRL_CHAR = '273e0001-4c4d-454d-96be-f03bac821358'
MUSE_TPCG_CHAR = '273e0008-4c4d-454d-96be-f03bac821358'  # PPG (Muse S)


class EEGSource:
    """Base class for EEG data sources."""
    def __init__(self, channels, sampling_rate, buffer_seconds=5):
        self.channels = channels
        self.n_channels = len(channels)
        self.sampling_rate = sampling_rate
        self.buffer = deque(maxlen=int(sampling_rate * buffer_seconds))
        self.running = False
        self._thread = None
        self.on_data = None  # callback(data: np.ndarray shape (n_channels, n_samples))

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def get_recent(self, seconds=2):
        n = min(int(self.sampling_rate * seconds), len(self.buffer))
        if n == 0:
            return np.zeros((self.n_channels, 1))
        return np.column_stack(list(self.buffer)[-n:])

    def _add_samples(self, samples):
        """Add one or more samples to the buffer.
        samples: np.ndarray shape (n_channels,) or (n_channels, n_samples)
        """
        if samples.ndim == 1:
            self.buffer.append(samples.copy())
        else:
            for i in range(samples.shape[1]):
                self.buffer.append(samples[:, i].copy())
        if self.on_data:
            self.on_data(samples)


class MuseSource(EEGSource):
    """Real Muse headband via Bluetooth LE using bleak."""

    def __init__(self, address=None, timeout=10):
        super().__init__(channels=MUSE_CHANNELS, sampling_rate=256)
        self.address = address
        self.timeout = timeout
        self._client = None
        self._packet_count = 0

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def _run(self):
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._connect_and_stream())
        except ImportError:
            log.error("bleak not installed. Run: pip install bleak")
            self.running = False
        except Exception as e:
            log.error(f"Muse error: {e}")
            self.running = False

    async def _connect_and_stream(self):
        from bleak import BleakScanner, BleakClient

        if self.address is None:
            log.info("Scanning for Muse devices...")
            devices = await BleakScanner.discover(timeout=self.timeout)
            muse_devices = [d for d in devices if 'muse' in (d.name or '').lower()]
            if not muse_devices:
                log.warning("No Muse devices found. Check headband is on and nearby.")
                self.running = False
                return
            self.address = muse_devices[0].address
            log.info(f"Found Muse: {muse_devices[0].name} ({self.address})")

        async with BleakClient(self.address, timeout=self.timeout) as client:
            log.info(f"Connected to Muse at {self.address}")
            await client.start_notify(MUSE_EEG_CHAR, self._handle_eeg)
            # Start data streaming
            await client.write_gatt_char(MUSE_CTRL_CHAR, bytearray([0x02, 0x64, 0x0a]))
            log.info("Muse EEG streaming started. Press Ctrl+C to stop.")
            while self.running:
                await asyncio.sleep(1)

    def _handle_eeg(self, sender, data):
        """Parse Muse BLE EEG notification."""
        try:
            if len(data) < 6:
                return
            packet_id = struct.unpack('>H', data[0:2])[0]
            timestamp = struct.unpack('<f', data[2:6])[0]
            samples_data = data[6:]
            samples_per_ch = len(samples_data) // (4 * 3)  # 4 ch × 3 bytes each
            if samples_per_ch == 0:
                return
            samples = np.zeros((4, samples_per_ch))
            for i in range(samples_per_ch):
                for ch in range(4):
                    offset = 6 + i * 12 + ch * 3
                    if offset + 3 <= len(data):
                        val = struct.unpack('<i', data[offset:offset+3] + b'\x00')[0]
                        val = val >> 8 if val > 0x7fffff else val  # sign extend
                        samples[ch, i] = val / 8388607.0  # normalize to -1..1
            self._packet_count += 1
            self._add_samples(samples)
        except Exception as e:
            log.warning(f"Parse error: {e}")

    def stop(self):
        self.running = False


class OpenBCISource(EEGSource):
    """Real OpenBCI Cyton/Daisy board via Serial."""

    def __init__(self, port='COM3', sampling_rate=250, n_channels=8):
        channels = OBCI_CHANNELS_8[:n_channels] if n_channels <= 8 else OBCI_CHANNELS_16
        super().__init__(channels=channels, sampling_rate=sampling_rate)
        self.port = port
        self.n_ch = n_channels
        self._serial = None

    def start(self):
        try:
            import serial
        except ImportError:
            log.error("pyserial not installed. Run: pip install pyserial")
            return self

        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def _run(self):
        import serial
        try:
            self._serial = serial.Serial(self.port, 115200, timeout=2)
            log.info(f"OpenBCI connected on {self.port}")
            # Wait for data
            while self.running:
                if self._serial.in_waiting >= 33:  # Standard OBCI packet
                    packet = self._serial.read(33)
                    samples = self._parse_packet(packet)
                    if samples is not None:
                        self._add_samples(samples)
        except serial.SerialException as e:
            log.error(f"Serial error on {self.port}: {e}")
        except Exception as e:
            log.error(f"OpenBCI error: {e}")
        finally:
            if self._serial:
                self._serial.close()

    def _parse_packet(self, packet):
        if packet[0] != 0xA0:
            return None
        samples = np.zeros(self.n_ch)
        for i in range(self.n_ch):
            offset = 1 + i * 3
            if offset + 3 <= len(packet):
                raw = struct.unpack('>i', packet[offset:offset+3] + b'\x00')[0]
                raw = raw >> 8
                samples[i] = raw / 8388607.0  # normalize
        return samples

    def stop(self):
        self.running = False
        if self._serial:
            self._serial.close()


class RecordedSource(EEGSource):
    """Play back a recorded EEG file for development/demo."""

    def __init__(self, filepath='bci/data/sample_eeg.bin', speed=1.0, loop=True):
        self.filepath = filepath
        self.speed = speed
        self.loop = loop
        self._data = None
        self._total_samples = 0
        fs, ch_names, data = self._load_file()
        super().__init__(channels=ch_names, sampling_rate=fs)
        self._data = data

    def _load_file(self):
        with open(self.filepath, 'rb') as f:
            header = f.read(8)
            fs, n = struct.unpack('ii', header)
            raw = np.frombuffer(f.read(), dtype=np.int16).astype(np.float32) / 32767.0
            data = raw.reshape(-1, n)  # channels × samples
        ch_names = MUSE_CHANNELS[:data.shape[0]]
        return fs, ch_names, data

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def _run(self):
        idx = 0
        samples_per_tick = max(1, int(self.sampling_rate * 0.05 * self.speed))
        while self.running:
            if idx + samples_per_tick > self._data.shape[1]:
                if self.loop:
                    idx = 0
                    log.info("Looping recorded EEG")
                else:
                    self.running = False
                    break
            chunk = self._data[:, idx:idx + samples_per_tick]
            self._add_samples(chunk)
            idx += samples_per_tick
            time.sleep(0.05 / self.speed)

    def stop(self):
        self.running = False


def create_source(source_type='recorded', **kwargs):
    """Factory: create an EEG source by type."""
    sources = {
        'muse': MuseSource,
        'openbci': OpenBCISource,
        'recorded': RecordedSource,
    }
    cls = sources.get(source_type)
    if cls is None:
        raise ValueError(f"Unknown source: {source_type}. Options: {list(sources.keys())}")
    return cls(**kwargs)
