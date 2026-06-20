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

public enum VisualState { Base, Transitional, Critical }

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

    [Header("Line Renderer (Fractal Dim History)")]
    public LineRenderer dimGraph;
    public int graphPoints = 128;
    public float graphHeight = 2.0f;
    public float graphWidth = 3.0f;

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

    [Header("Audio Feedback")]
    public AudioSource audioSource;
    public float basePitch = 0.8f;
    public float pitchRange = 1.2f;

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
    public VisualState visualState = VisualState.Base;

    private ClientWebSocket ws;
    private CancellationTokenSource cts;
    private readonly Queue<CognitiveData> pendingData = new Queue<CognitiveData>();
    private Color targetColor = Color.magenta;
    private Color baseColor = new Color(0.1f, 0.4f, 1.0f);    // blue
    private Color transitionalColor = new Color(0.6f, 0.1f, 0.9f); // purple
    private Color criticalColor = new Color(1.0f, 0.1f, 0.1f);    // red
    private Vector3 targetScale = Vector3.one;
    private float targetRotationSpeed = 10f;
    private Vector3 cameraOriginPosition;
    private float currentShakeTime = 0f;
    private float currentShakeIntensity = 0f;
    private float glitchTarget = 0f;
    private float elapsedTime = 0f;
    private Material overlayMaterial;

    // Fractal dimension history for line graph
    private float[] dimHistory;
    private int dimIndex = 0;

    // Terminal overlay
    private Texture2D terminalTex;
    private Color[] terminalPixels;
    private int termWidth = 128;
    private int termHeight = 72;
    private float[] termChars;
    private float[] termBrightness;

    async void Start()
    {
        if (mainCamera != null)
        {
            cameraOriginPosition = mainCamera.transform.localPosition;
            Debug.Log("[FCSTN] Camera found: " + mainCamera.name);
        }
        else if (Camera.main != null)
        {
            mainCamera = Camera.main;
            cameraOriginPosition = mainCamera.transform.localPosition;
            Debug.Log("[FCSTN] Using Main Camera");
        }
        else
        {
            Debug.LogWarning("[FCSTN] No camera assigned!");
        }

        if (glitchMaterial != null)
        {
            overlayMaterial = new Material(glitchMaterial);
            Debug.Log("[FCSTN] Glitch material created");
        }
        else
        {
            Debug.LogWarning("[FCSTN] No glitch material assigned");
        }

        if (fractalMesh != null) Debug.Log("[FCSTN] Fractal mesh: " + fractalMesh.name);
        if (sceneLight != null) Debug.Log("[FCSTN] Light: " + sceneLight.name);
        if (fractalParticles != null) Debug.Log("[FCSTN] Fractal particles: " + fractalParticles.name);
        if (glitchParticles != null) Debug.Log("[FCSTN] Glitch particles: " + glitchParticles.name);

        dimHistory = new float[graphPoints];
        for (int i = 0; i < graphPoints; i++) dimHistory[i] = 2.5f;

        if (dimGraph != null)
        {
            dimGraph.positionCount = graphPoints;
            dimGraph.startWidth = 0.04f;
            dimGraph.endWidth = 0.01f;
            dimGraph.material = new Material(Shader.Find("Sprites/Default"));
            dimGraph.startColor = Color.cyan;
            dimGraph.endColor = Color.magenta;
        }

        InitTerminalOverlay();

        cts = new CancellationTokenSource();
        _ = ConnectAndListen();
    }

    void InitTerminalOverlay()
    {
        terminalTex = new Texture2D(termWidth, termHeight, TextureFormat.RGBA32, false);
        terminalPixels = new Color[termWidth * termHeight];
        termChars = new float[termWidth * termHeight];
        termBrightness = new float[termWidth * termHeight];
        for (int i = 0; i < termChars.Length; i++)
        {
            termChars[i] = Random.value;
            termBrightness[i] = Random.Range(0.1f, 0.8f);
        }
    }

    void UpdateTerminalOverlay()
    {
        float chaos = Mathf.Lerp(0.01f, 0.15f, glitchTarget);
        for (int y = 0; y < termHeight; y++)
        {
            for (int x = 0; x < termWidth; x++)
            {
                int idx = y * termWidth + x;
                if (Random.value < chaos)
                {
                    termChars[idx] = Random.value;
                    termBrightness[idx] = Random.Range(0.3f, 1.0f);
                }
                float b = termBrightness[idx] * (1f - Mathf.Abs(y - termHeight / 2f) / termHeight * 0.5f);
                Color c = Color.Lerp(currentColor, Color.white, b * 0.3f) * b;
                c.a = b * Mathf.Lerp(0.3f, 0.8f, glitchTarget);
                terminalPixels[idx] = c;
            }
        }
        terminalTex.SetPixels(terminalPixels);
        terminalTex.Apply();

        if (overlayMaterial != null)
        {
            overlayMaterial.SetTexture("_TerminalTex", terminalTex);
            overlayMaterial.SetFloat("_TerminalOpacity", Mathf.Lerp(0f, 0.4f, glitchTarget));
        }
    }

    int _reconnectCount = 0;
    int _msgCount = 0;

    async Task ConnectAndListen()
    {
        ws = new ClientWebSocket();
        try
        {
            Debug.Log("[FCSTN] Connecting to " + serverUrl + "... (attempt " + (_reconnectCount + 1) + ")");
            await ws.ConnectAsync(new Uri(serverUrl), cts.Token);
            Debug.Log("[FCSTN] Connected!");
            _reconnectCount = 0;

            byte[] buffer = new byte[16384];

            while (ws.State == WebSocketState.Open && !cts.Token.IsCancellationRequested)
            {
                var result = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), cts.Token);
                if (result.MessageType == WebSocketMessageType.Close)
                {
                    Debug.LogWarning("[FCSTN] Server closed connection");
                    await ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
                    break;
                }
                string json = Encoding.UTF8.GetString(buffer, 0, result.Count);
                _msgCount++;
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

        _reconnectCount++;
        Debug.Log("[FCSTN] Reconnecting in 3s... (attempts=" + _reconnectCount + ", msgs=" + _msgCount + ")");
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
        catch (Exception ex)
        {
            Debug.LogWarning("[FCSTN] Payload parse skipped: " + ex.Message);
        }

        try
        {
            var dict = JsonUtility.FromJson<CognitiveData>(json);
            if (dict.attention > 0 || dict.fractal_dimension > 0)
            {
                lock (pendingData)
                {
                    pendingData.Enqueue(dict);
                }
            }
        }
        catch (Exception ex)
        {
            Debug.LogWarning("[FCSTN] Direct data parse skipped: " + ex.Message);
        }
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
            if (data.state_name != stateName)
                Debug.Log("[FCSTN] State: " + data.state_name + " | attn=" + data.attention.ToString("F2") + " eng=" + data.engagement.ToString("F2") + " load=" + data.workload.ToString("F2"));
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

            dimHistory[dimIndex % graphPoints] = fractalDimension;
            dimIndex++;
        }

        UpdateVisualState();
        UpdateFractalMesh();
        UpdateParticles();
        UpdateCameraShake();
        UpdateLighting();
        UpdateDimGraph();
        UpdateTerminalOverlay();

        glitchIntensity = Mathf.Lerp(glitchIntensity, glitchTarget, Time.deltaTime * 2f);

        if (audioSource != null && audioSource.isActiveAndEnabled)
        {
            audioSource.pitch = Mathf.Lerp(basePitch, basePitch + pitchRange, workload);
            audioSource.volume = Mathf.Lerp(0.1f, 0.6f, glitchTarget);
        }
    }

    void UpdateVisualState()
    {
        VisualState prev = visualState;
        if (workload > 0.7f || glitchTarget > 0.5f)
            visualState = VisualState.Critical;
        else if (workload > 0.4f || engagement > 0.7f)
            visualState = VisualState.Transitional;
        else
            visualState = VisualState.Base;

        if (prev != visualState)
            Debug.Log("[FCSTN] Visual State: " + visualState);

        Color stateColor;
        switch (visualState)
        {
            case VisualState.Critical:
                stateColor = Color.Lerp(targetColor, criticalColor, 0.5f);
                break;
            case VisualState.Transitional:
                stateColor = Color.Lerp(targetColor, transitionalColor, 0.3f);
                break;
            default:
                stateColor = Color.Lerp(targetColor, baseColor, 0.2f);
                break;
        }
        targetColor = Color.Lerp(targetColor, stateColor, 0.3f);
    }

    void UpdateFractalMesh()
    {
        if (fractalMesh == null) return;
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
            if (renderer.material.HasProperty("_Glossiness"))
            {
                renderer.material.SetFloat("_Glossiness", Mathf.Lerp(0.2f, 1.0f, coherence));
            }
            if (renderer.material.HasProperty("_Metallic"))
            {
                renderer.material.SetFloat("_Metallic", Mathf.Lerp(0f, 0.8f, workload));
            }
        }
    }

    void UpdateParticles()
    {
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
    }

    void UpdateCameraShake()
    {
        if (mainCamera == null) return;
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

    void UpdateLighting()
    {
        if (sceneLight == null) return;
        sceneLight.color = Color.Lerp(sceneLight.color, targetColor, Time.deltaTime * colorSpeed * 0.5f);
        sceneLight.intensity = Mathf.Lerp(0.8f, 3.0f, attention);
    }

    void UpdateDimGraph()
    {
        if (dimGraph == null) return;
        int count = Mathf.Min(graphPoints, dimIndex);
        for (int i = 0; i < count; i++)
        {
            int idx = (dimIndex - count + i) % graphPoints;
            float x = (float)i / count * graphWidth - graphWidth / 2f;
            float y = (dimHistory[idx] - 2f) / 2f * graphHeight;
            dimGraph.SetPosition(i, new Vector3(x, y, 2f));
        }
        for (int i = count; i < graphPoints; i++)
        {
            dimGraph.SetPosition(i, Vector3.zero);
        }

        float graphOpacity = Mathf.Lerp(0.05f, 0.6f, glitchTarget + attention * 0.3f);
        dimGraph.startColor = new Color(currentColor.r, currentColor.g, currentColor.b, graphOpacity);
        dimGraph.endColor = new Color(currentColor.r * 0.5f, 0f, currentColor.b, graphOpacity * 0.3f);
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
