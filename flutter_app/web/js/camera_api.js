// FCSTN Camera Emotion Detection using face-api.js
let fcstn = {
  video: null,
  canvas: null,
  stream: null,
  ready: false,
  active: false,
  lastResult: null,
  detectionCount: 0
};

function _dist(a, b) {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
}

async function fcstnInitCamera() {
  try {
    fcstn.video = document.createElement('video');
    fcstn.video.setAttribute('autoplay', '');
    fcstn.video.setAttribute('playsinline', '');
    fcstn.video.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:320px;height:240px';
    document.body.appendChild(fcstn.video);

    fcstn.canvas = document.createElement('canvas');
    fcstn.canvas.style.display = 'none';
    document.body.appendChild(fcstn.canvas);

    fcstn.stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 320, height: 240, facingMode: 'user' }
    });
    fcstn.video.srcObject = fcstn.stream;
    await fcstn.video.play();

    const MODEL_URL = 'https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/weights';
    await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
    await faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL);
    await faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL);

    fcstn.ready = true;
    fcstn.active = true;
    return JSON.stringify({ status: 'ok' });
  } catch (e) {
    return JSON.stringify({ status: 'error', message: e.message || String(e) });
  }
}

async function fcstnDetect() {
  if (!fcstn.ready || !fcstn.active || !fcstn.video) {
    return JSON.stringify({ status: 'not_ready' });
  }
  try {
    const result = await faceapi
      .detectSingleFace(fcstn.video, new faceapi.TinyFaceDetectorOptions({ inputSize: 160 }))
      .withFaceLandmarks()
      .withFaceExpressions();

    if (!result) {
      return JSON.stringify({ status: 'no_face' });
    }

    fcstn.detectionCount++;

    const expressions = result.expressions;
    let dominant = 'neutral', maxProb = 0;
    for (const [emotion, prob] of Object.entries(expressions)) {
      if (prob > maxProb) { maxProb = prob; dominant = emotion; }
    }

    const lm = result.landmarks.positions;
    const le = lm[36], re = lm[45];
    const ml = lm[48], mr = lm[54], mt = lm[51], mb = lm[57];
    const et = lm[37], eb = lm[41];
    const et2 = lm[43], eb2 = lm[47];

    const ear = (_dist(et, eb) + _dist(et2, eb2)) / (2 * _dist(le, re) || 1);
    const mouthRatio = _dist(mt, mb) / (_dist(ml, mr) || 1);
    const faceW = _dist(le, re) * 2.5;
    const noseOff = (lm[30].x - (le.x + re.x) / 2) / (faceW / 2 || 1);
    const brow = _dist(lm[17], lm[21]) / (faceW || 1);

    const metrics = {
      status: 'ok',
      emotion: dominant,
      probability: Math.round(maxProb * 1000) / 1000,
      happy: Math.round((expressions.happy || 0) * 1000) / 1000,
      sad: Math.round((expressions.sad || 0) * 1000) / 1000,
      angry: Math.round((expressions.angry || 0) * 1000) / 1000,
      fearful: Math.round((expressions.fearful || 0) * 1000) / 1000,
      surprised: Math.round((expressions.surprised || 0) * 1000) / 1000,
      disgusted: Math.round((expressions.disgusted || 0) * 1000) / 1000,
      neutral: Math.round((expressions.neutral || 0) * 1000) / 1000,
      ear: Math.round(ear * 1000) / 1000,
      mouthRatio: Math.round(mouthRatio * 1000) / 1000,
      noseOffset: Math.round(noseOff * 1000) / 1000,
      browRaise: Math.round(brow * 1000) / 1000,
      detections: fcstn.detectionCount,
      faceBox: {
        x: Math.round(result.detection.box.x),
        y: Math.round(result.detection.box.y),
        w: Math.round(result.detection.box.width),
        h: Math.round(result.detection.box.height)
      }
    };

    fcstn.lastResult = metrics;
    return JSON.stringify(metrics);
  } catch (e) {
    return JSON.stringify({ status: 'error', message: e.message || String(e) });
  }
}

function fcstnStopCamera() {
  fcstn.active = false;
  if (fcstn.stream) { fcstn.stream.getTracks().forEach(t => t.stop()); }
  if (fcstn.video) { fcstn.video.remove(); fcstn.video = null; }
  if (fcstn.canvas) { fcstn.canvas.remove(); fcstn.canvas = null; }
  fcstn.ready = false;
  return JSON.stringify({ status: 'stopped' });
}

function fcstnGetLastResult() {
  return fcstn.lastResult
    ? JSON.stringify(fcstn.lastResult)
    : JSON.stringify({ status: 'no_data' });
}
