using System;
using System.Collections;
using System.Collections.Generic;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.Rendering;
using Random = UnityEngine.Random;

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
    public float load;
    public float workload;
    public float valence;
    public float coherence;
    public float fractal_dimension;
    public float fractal_dim;
    public string state_name;
    public string phase;
    public string color;
    public float complexity;
    public float instability;
    public double timestamp;
    public string narrative;
    public string image_prompt;
}

public class FCSTNClient : MonoBehaviour
{
    [Header("Connection")]
    public string serverUrl = "ws://localhost:8765";

    [Header("Target Objects")]
    public Transform fractalMesh;
    public Light sceneLight;
    public ParticleSystem fractalParticles;
    public ParticleSystem glitchParticles;
    public Camera mainCamera;

    [Header("Visualization Settings")]
    public float scaleSpeed = 3f;
    public float colorSpeed = 3f;
    public float rotationSpeed = 10f;

    [Header("Camera Shake")]
    public float shakeIntensityMultiplier = 0.5f;
    public float shakeDecay = 1.5f;

    [Header("Glitch Overlay")]
    public Material glitchMaterial;
    public float glitchIntensity = 0f;

    [Header("Live Metrics (Read Only)")]
    public float attention = 0.5f;
    public float engagement = 0.5f;
    public float workload = 0.3f;
    public float fractalDimension = 2.5f;
    public float valence = 0.5f;
    public float coherence = 0.5f;
    public string stateName = "resting";
    public Color currentColor = Color.magenta;
    public string lastNarrative = "";
    public string lastImagePrompt = "";

    private ClientWebSocket ws;
    private CancellationTokenSource cts;
    private readonly Queue<CognitiveData> pendingData = new Queue<CognitiveData>();
    private Color targetColor = Color.magenta;
    private Vector3 targetScale = Vector3.one;
    private float targetRotationSpeed = 10f;
    private Vector3 cameraOriginPosition;
    private float currentShakeTime = 0f;
    private float currentShakeIntensity = 0f;
    private float glitchTarget = 0f;
    private float elapsedTime = 0f;
    private Material overlayMaterial;

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

        if (glitchMaterial != null)
        {
            overlayMaterial = new Material(glitchMaterial);
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
            Debug.Log("[FCSTN] Connected!");

            byte[] buffer = new byte[16384];

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
            ws?.Dispose();
        }

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
            if (payload.type == "state" || payload.type == "cognitive_state")
            {
                lock (pendingData)
                {
                    pendingData.Enqueue(payload.data);
                }
                return;
            }
        }
        catch { }

        try
        {
            CognitiveData directData = JsonUtility.FromJson<CognitiveData>(json);
            if (directData.attention > 0 || directData.fractal_dimension > 0)
            {
                lock (pendingData)
                {
                    pendingData.Enqueue(directData);
                }
            }
        }
        catch { }
    }

    void Update()
    {
        elapsedTime += Time.deltaTime;

        CognitiveData data = default;
        bool hasNewData = false;
        lock (pendingData)
        {
            if (pendingData.Count > 0)
            {
                data = pendingData.Dequeue();
                hasNewData = true;
            }
        }

        if (hasNewData)
        {
            attention = data.attention;
            engagement = data.engagement;
            workload = Mathf.Max(data.load, data.workload);
            fractalDimension = Mathf.Max(data.fractal_dimension, data.fractal_dim);
            valence = data.valence;
            coherence = data.coherence;
            stateName = data.state_name;
            lastNarrative = data.narrative;
            lastImagePrompt = data.image_prompt;

            if (ColorUtility.TryParseHtmlString(data.color, out Color parsedColor))
                targetColor = parsedColor;

            float scale = 1f + (fractalDimension - 2f) * 2.5f + engagement * 2.0f;
            targetScale = new Vector3(scale, scale, scale);
            targetRotationSpeed = 10f + data.instability * 80f;

            if (workload > 0.75f)
            {
                currentShakeIntensity = (workload - 0.7f) * shakeIntensityMultiplier * 2f;
                currentShakeTime = 0.6f;
            }

            glitchTarget = workload * 0.5f + Mathf.Max(0, (attention - 0.8f)) * 0.5f;
        }

        if (fractalMesh != null)
        {
            fractalMesh.localScale = Vector3.Lerp(fractalMesh.localScale, targetScale, Time.deltaTime * scaleSpeed);
            fractalMesh.Rotate(Vector3.up, targetRotationSpeed * Time.deltaTime);
            fractalMesh.Rotate(Vector3.right, (targetRotationSpeed * 0.3f) * Time.deltaTime);
            fractalMesh.Rotate(Vector3.forward, (targetRotationSpeed * 0.15f) * Time.deltaTime);

            Renderer renderer = fractalMesh.GetComponent<Renderer>();
            if (renderer != null)
            {
                currentColor = Color.Lerp(currentColor, targetColor, Time.deltaTime * colorSpeed);
                renderer.material.color = currentColor;
                if (renderer.material.HasProperty("_EmissionColor"))
                {
                    renderer.material.SetColor("_EmissionColor", currentColor * (0.3f + attention * 0.7f));
                }
            }
        }

        if (fractalParticles != null)
        {
            var mainModule = fractalParticles.main;
            var emissionModule = fractalParticles.emission;
            var noiseModule = fractalParticles.noise;
            var colorOverLifetime = fractalParticles.colorOverLifetime;
            var sizeOverLifetime = fractalParticles.sizeOverLifetime;

            mainModule.simulationSpeed = Mathf.Lerp(0.5f, 6.0f, engagement);
            mainModule.startColor = currentColor;
            emissionModule.rateOverTime = Mathf.Lerp(20f, 500f, attention);

            if (noiseModule.enabled || workload > 0.2f)
            {
                noiseModule.enabled = true;
                noiseModule.strength = Mathf.Lerp(0.05f, 4.0f, workload);
                noiseModule.frequency = Mathf.Lerp(0.3f, 2.0f, workload);
                noiseModule.scrollSpeed = Mathf.Lerp(0.1f, 3.0f, engagement);
            }

            if (coherence > 0.6f)
            {
                var grad = new Gradient();
                grad.SetKeys(
                    new GradientColorKey[] {
                        new GradientColorKey(currentColor, 0f),
                        new GradientColorKey(Color.Lerp(currentColor, Color.white, 0.3f), 0.5f),
                        new GradientColorKey(currentColor, 1f)
                    },
                    new GradientAlphaKey[] {
                        new GradientAlphaKey(1f, 0f),
                        new GradientAlphaKey(0.5f, 0.5f),
                        new GradientAlphaKey(0f, 1f)
                    }
                );
                colorOverLifetime.color = new ParticleSystem.MinMaxGradient(grad);
            }
        }

        if (glitchParticles != null)
        {
            var glitchEmission = glitchParticles.emission;
            glitchEmission.rateOverTime = Mathf.Lerp(0f, 100f, glitchTarget);
            var glitchMain = glitchParticles.main;
            glitchMain.startColor = Color.Lerp(Color.red, Color.cyan, attention);
            glitchMain.simulationSpeed = Mathf.Lerp(0.5f, 4f, workload);
        }

        if (mainCamera != null)
        {
            if (currentShakeTime > 0)
            {
                Vector3 randomOffset = Random.insideUnitSphere * currentShakeIntensity;
                mainCamera.transform.localPosition = cameraOriginPosition + randomOffset;
                mainCamera.transform.localRotation = Quaternion.Euler(
                    Random.Range(-currentShakeIntensity * 5f, currentShakeIntensity * 5f),
                    Random.Range(-currentShakeIntensity * 3f, currentShakeIntensity * 3f),
                    0
                );
                currentShakeTime -= Time.deltaTime;
                currentShakeIntensity = Mathf.Lerp(currentShakeIntensity, 0f, Time.deltaTime * shakeDecay);
            }
            else
            {
                mainCamera.transform.localPosition = Vector3.Lerp(
                    mainCamera.transform.localPosition, cameraOriginPosition, Time.deltaTime * 5f);
                mainCamera.transform.localRotation = Quaternion.Lerp(
                    mainCamera.transform.localRotation, Quaternion.identity, Time.deltaTime * 3f);
            }
        }

        if (sceneLight != null)
        {
            sceneLight.color = Color.Lerp(sceneLight.color, targetColor, Time.deltaTime * colorSpeed * 0.5f);
            sceneLight.intensity = Mathf.Lerp(0.8f, 3.0f, attention);
        }

        glitchIntensity = Mathf.Lerp(glitchIntensity, glitchTarget, Time.deltaTime * 2f);
    }

    void OnRenderImage(RenderTexture source, RenderTexture destination)
    {
        if (overlayMaterial != null && glitchIntensity > 0.01f)
        {
            overlayMaterial.SetFloat("_GlitchIntensity", glitchIntensity);
            overlayMaterial.SetFloat("_TimeOffset", elapsedTime);
            overlayMaterial.SetColor("_GlitchColor", currentColor);
            Graphics.Blit(source, destination, overlayMaterial);
        }
        else
        {
            Graphics.Blit(source, destination);
        }
    }

    void OnDestroy()
    {
        cts?.Cancel();
        ws?.Dispose();
        if (overlayMaterial != null)
            Destroy(overlayMaterial);
    }
}
