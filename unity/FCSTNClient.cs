using System;
using System.Collections;
using System.Collections.Generic;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

[System.Serializable]
public struct CognitivePayload
{
    public string type;
    public CognitiveData data;
}

[System.Serializable]
public struct CognitiveData
{
    public float attention;
    public float engagement;
    public float workload;
    public float fractal_dim;
    public string state_name;
    public string color;
    public float complexity;
    public float instability;
    public double timestamp;
    public string narrative;      // Dynamic AI narrative text
    public string image_prompt;   // Generative world-seed prompt
}

public class FCSTNClient : MonoBehaviour
{
    [Header("Connection")]
    public string serverUrl = "ws://localhost:8765";

    [Header("Target Objects")]
    public Transform fractalMesh;
    public Light sceneLight;
    public ParticleSystem fractalParticles; // System of particles representing neurons/chaos
    public Camera mainCamera;               // Main camera to apply dynamic shake effects

    [Header("Visualization Settings")]
    public float scaleSpeed = 3f;
    public float colorSpeed = 3f;
    public float rotationSpeed = 10f;

    [Header("Camera Shake Settings")]
    public float shakeIntensityMultiplier = 0.5f;
    public float shakeDecay = 1.5f;

    // Runtime cognitive state
    [Header("Live Metrics (Read Only)")]
    public float attention = 0.5f;
    public float engagement = 0.5f;
    public float workload = 0.3f;
    public float fractalDimension = 2.5f;
    public string stateName = "neutral";
    public Color currentColor = Color.magenta;
    public string lastNarrative = "";
    public string lastImagePrompt = "";

    private ClientWebSocket ws;
    private CancellationTokenSource cts;
    private Queue<CognitiveData> pendingData = new Queue<CognitiveData>();
    private Color targetColor = Color.magenta;
    private Vector3 targetScale = Vector3.one;
    private float targetRotationSpeed = 10f;

    // Camera shake fields
    private Vector3 cameraOriginPosition;
    private float currentShakeTime = 0f;
    private float currentShakeIntensity = 0f;

    async void Start()
    {
        if (mainCamera != null)
        {
            cameraOriginPosition = mainCamera.transform.localPosition;
        }
        else if (Camera.main != null)
        {
            mainCamera = Camera.main;
            cameraOriginPosition = mainCamera.transform.localPosition;
        }

        cts = new CancellationTokenSource();
        _ = ConnectAndListen();
    }

    async Task ConnectAndListen()
    {
        ws = new ClientWebSocket();
        try
        {
            Debug.Log("[FCSTN] Connecting to " + serverUrl + "...");
            await ws.ConnectAsync(new Uri(serverUrl), cts.Token);
            Debug.Log("[FCSTN] Connected to FCSTN Server!");

            byte[] buffer = new byte[16384]; // Increased buffer size for rich AI payloads

            while (ws.State == WebSocketState.Open && !cts.Token.IsCancellationRequested)
            {
                var result = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), cts.Token);

                if (result.MessageType == WebSocketMessageType.Close)
                {
                    await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
                    break;
                }

                string json = Encoding.UTF8.GetString(buffer, 0, result.Count);
                ProcessMessage(json);
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[FCSTN] Connection error: " + e.Message);
        }
        finally
        {
            if (ws != null)
                ws.Dispose();
        }

        // Reconnect after 3s
        Debug.Log("[FCSTN] Reconnecting in 3s...");
        await Task.Delay(3000);
        if (!cts.Token.IsCancellationRequested)
            _ = ConnectAndListen();
    }

    void ProcessMessage(string json)
    {
        try
        {
            CognitivePayload payload = JsonUtility.FromJson<CognitivePayload>(json);
            // Support both standard envelope or direct data
            if (payload.type == "state" || payload.type == "cognitive_state")
            {
                lock (pendingData)
                {
                    pendingData.Enqueue(payload.data);
                }
            }
            else
            {
                // Fallback attempt to parse data directly if sent without type envelope
                CognitiveData directData = JsonUtility.FromJson<CognitiveData>(json);
                if (directData.attention > 0 || directData.fractal_dim > 0)
                {
                    lock (pendingData)
                    {
                        pendingData.Enqueue(directData);
                    }
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogWarning("[FCSTN] Parse error: " + e.Message);
        }
    }

    void Update()
    {
        // Process pending data on main thread
        CognitiveData data;
        bool hasNewData = false;
        lock (pendingData)
        {
            if (pendingData.Count > 0)
            {
                data = pendingData.Dequeue();
                hasNewData = true;
            }
            else
            {
                data = new CognitiveData();
            }
        }

        if (hasNewData)
        {
            // Update runtime metrics
            attention = data.attention;
            engagement = data.engagement;
            workload = data.workload;
            fractalDimension = data.fractal_dim;
            stateName = data.state_name;
            lastNarrative = data.narrative;
            lastImagePrompt = data.image_prompt;

            // Parse color
            if (ColorUtility.TryParseHtmlString(data.color, out Color parsedColor))
                targetColor = parsedColor;

            // Calculate target scale based on fractal dimension and engagement
            float scale = 1f + (fractalDimension - 2f) * 2.5f + engagement * 2.0f;
            targetScale = new Vector3(scale, scale, scale);

            // Rotation speed based on instability
            targetRotationSpeed = 10f + data.instability * 80f;

            // Trigger Camera Shake if workload is high
            if (workload > 0.75f)
            {
                currentShakeIntensity = (workload - 0.7f) * shakeIntensityMultiplier;
                currentShakeTime = 0.5f; // Shake for half a second
            }
        }

        // Apply smooth transformations to the core fractal mesh
        if (fractalMesh != null)
        {
            fractalMesh.localScale = Vector3.Lerp(fractalMesh.localScale, targetScale, Time.deltaTime * scaleSpeed);
            fractalMesh.Rotate(Vector3.up, targetRotationSpeed * Time.deltaTime);
            fractalMesh.Rotate(Vector3.right, (targetRotationSpeed * 0.3f) * Time.deltaTime);

            Renderer renderer = fractalMesh.GetComponent<Renderer>();
            if (renderer != null)
            {
                currentColor = Color.Lerp(currentColor, targetColor, Time.deltaTime * colorSpeed);
                renderer.material.color = currentColor;
                renderer.material.SetColor("_EmissionColor", currentColor * (0.3f + attention * 0.7f));
            }
        }

        // Update Particle System parameters dynamically (Wow factor)
        if (fractalParticles != null)
        {
            var mainModule = fractalParticles.main;
            var emissionModule = fractalParticles.emission;
            var noiseModule = fractalParticles.noise;

            // Speed of particles reflects the cognitive engagement
            mainModule.simulationSpeed = Mathf.Lerp(0.5f, 5.0f, engagement);
            
            // Start color matches the network's color
            mainModule.startColor = currentColor;

            // Number of active particles matches the audience attention
            emissionModule.rateOverTime = Mathf.Lerp(15f, 350f, attention);

            // Chaos in particles matches the mental workload (system instability)
            if (noiseModule.enabled || workload > 0.3f)
            {
                noiseModule.enabled = true;
                noiseModule.strength = Mathf.Lerp(0.05f, 3.5f, workload);
            }
        }

        // Handle Camera Shake
        if (mainCamera != null)
        {
            if (currentShakeTime > 0)
            {
                Vector3 randomOffset = UnityEngine.Random.insideUnitSphere * currentShakeIntensity;
                mainCamera.transform.localPosition = cameraOriginPosition + randomOffset;
                currentShakeTime -= Time.deltaTime;
                currentShakeIntensity = Mathf.Lerp(currentShakeIntensity, 0f, Time.deltaTime * shakeDecay);
            }
            else
            {
                mainCamera.transform.localPosition = Vector3.Lerp(mainCamera.transform.localPosition, cameraOriginPosition, Time.deltaTime * 5f);
            }
        }

        // Update light color
        if (sceneLight != null)
        {
            sceneLight.color = Color.Lerp(sceneLight.color, targetColor, Time.deltaTime * colorSpeed * 0.5f);
            sceneLight.intensity = 0.8f + attention * 2.0f;
        }
    }

    void OnDestroy()
    {
        cts?.Cancel();
        ws?.Dispose();
    }
}
