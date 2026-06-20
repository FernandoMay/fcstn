Shader "Hidden/FCSTNGlitch"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _GlitchIntensity ("Glitch Intensity", Range(0, 1)) = 0
        _TimeOffset ("Time Offset", Float) = 0
        _GlitchColor ("Glitch Color", Color) = (1, 0, 0, 1)
    }
    SubShader
    {
        Cull Off ZWrite Off ZTest Always
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                float2 uv : TEXCOORD0;
            };

            struct v2f
            {
                float2 uv : TEXCOORD0;
                float4 vertex : SV_POSITION;
            };

            v2f vert (appdata v)
            {
                v2f o;
                o.vertex = UnityObjectToClipPos(v.vertex);
                o.uv = v.uv;
                return o;
            }

            sampler2D _MainTex;
            float _GlitchIntensity;
            float _TimeOffset;
            float4 _GlitchColor;

            fixed4 frag (v2f i) : SV_Target
            {
                fixed4 col = tex2D(_MainTex, i.uv);

                float t = _TimeOffset * 13.37;
                float glitchLine = sin(i.uv.y * 240 + t) * 0.5 + 0.5;
                float glitchAmount = glitchLine * _GlitchIntensity;

                if (glitchAmount > 0.95)
                {
                    float2 offset = float2(
                        sin(i.uv.y * 666 + t * 1.7) * 0.05 * _GlitchIntensity,
                        0
                    );
                    col = tex2D(_MainTex, i.uv + offset);
                    col.rgb = lerp(col.rgb, _GlitchColor.rgb, _GlitchIntensity * 0.3);
                }

                float scanline = sin(i.uv.y * 480) * 0.02 + 0.98;
                col.rgb *= scanline;

                float vignette = 1.0 - length(i.uv - 0.5) * 0.8;
                col.rgb *= vignette;

                return col;
            }
            ENDCG
        }
    }
}
