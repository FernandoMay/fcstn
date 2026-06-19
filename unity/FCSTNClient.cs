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
}

public class FCSTNClient : MonoBehaviour
{
    [Header("Connection")]
    public string serverUrl = "ws://localhost:8765";

    [Header("Target Objects")]
    public Transform fractalMesh;
    public Light sceneLight;

    [Header("Visualization Settings")]
    public float scaleSpeed = 3f;
    public float colorSpeed = 3f;
    public float rotationSpeed = 10f;

    // Runtime cognitive state
    [Header("Live Metrics (Read Only)")]
    public float attention = 0.5f;
    public float engagement = 0.5f;
    public float workload = 0.3f;
    public float fractalDimension = 2.5f;
    public string stateName = "neutral";
    public Color currentColor = Color.magenta;

    private ClientWebSocket ws;
    private CancellationTokenSource cts;
    private Queue<CognitiveData> pendingData = new Queue<CognitiveData>();
    private Color targetColor = Color.magenta;
    private Vector3 targetScale = Vector3.one;
    private float targetRotationSpeed = 10f;

    async void Start()
    {
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

            byte[] buffer = new byte[8192];

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
            if (payload.type == "state")
            {
                lock (pendingData)
                {
                    pendingData.Enqueue(payload.data);
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
        lock (pendingData)
        {
            if (pendingData.Count > 0)
                data = pendingData.Dequeue();
            else
                return;
        }

        // Update runtime metrics
        attention = data.attention;
        engagement = data.engagement;
        workload = data.workload;
        fractalDimension = data.fractal_dim;
        stateName = data.state_name;

        // Parse color
        if (ColorUtility.TryParseHtmlString(data.color, out Color parsedColor))
            targetColor = parsedColor;

        // Calculate target scale based on fractal dimension and engagement
        float scale = 1f + (fractalDimension - 2f) * 2f + engagement * 1.5f;
        targetScale = new Vector3(scale, scale, scale);

        // Rotation speed based on instability
        targetRotationSpeed = 10f + data.instability * 40f;

        // Apply smooth transformations
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
                renderer.material.SetColor("_EmissionColor", currentColor * 0.5f);
            }
        }

        // Update light color
        if (sceneLight != null)
        {
            sceneLight.color = Color.Lerp(sceneLight.color, targetColor, Time.deltaTime * colorSpeed * 0.5f);
            sceneLight.intensity = 1f + attention * 1.5f;
        }
    }

    void OnDestroy()
    {
        cts?.Cancel();
        ws?.Dispose();
    }
}
