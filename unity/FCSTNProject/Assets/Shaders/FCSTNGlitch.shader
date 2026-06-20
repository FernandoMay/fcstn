Shader "Hidden/FCSTNGlitch"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _GlitchIntensity ("Glitch Intensity", Range(0, 1)) = 0
        _TimeOffset ("Time Offset", Float) = 0
        _GlitchColor ("Glitch Color", Color) = (1, 0, 0, 1)
        _TerminalTex ("Terminal Overlay", 2D) = "black" {}
        _TerminalOpacity ("Terminal Opacity", Range(0, 1)) = 0
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
            sampler2D _TerminalTex;
            float _GlitchIntensity;
            float _TimeOffset;
            float4 _GlitchColor;
            float _TerminalOpacity;

            fixed4 frag (v2f i) : SV_Target
            {
                float t = _TimeOffset * 13.37;
                float glitchLine = sin(i.uv.y * 240 + t) * 0.5 + 0.5;
                float glitchAmount = glitchLine * _GlitchIntensity;

                float splitAmount = _GlitchIntensity * 0.02;
                float r_offset = sin(i.uv.y * 480 + t * 0.7) * splitAmount;
                float b_offset = cos(i.uv.y * 480 + t * 0.5) * splitAmount;

                fixed4 col_r = tex2D(_MainTex, i.uv + float2(r_offset, 0));
                fixed4 col_g = tex2D(_MainTex, i.uv);
                fixed4 col_b = tex2D(_MainTex, i.uv + float2(b_offset, 0));

                fixed4 col;
                col.r = col_r.r;
                col.g = col_g.g;
                col.b = col_b.b;
                col.a = 1.0;

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

                float2 center = i.uv - 0.5;
                float vignette = 1.0 - dot(center, center) * 1.2;
                col.rgb *= vignette;

                if (_GlitchIntensity > 0.3)
                {
                    float blockLine = sin(i.uv.y * 24 + t * 3.0) * 0.5 + 0.5;
                    float blockAmount = step(0.95 - _GlitchIntensity * 0.4, blockLine);
                    float2 blockOffset = float2(
                        (sin(i.uv.y * 40 + t * 2.0) * 0.5 + 0.5) * _GlitchIntensity * 0.03,
                        0
                    );
                    fixed4 blockCol = tex2D(_MainTex, i.uv + blockOffset);
                    col = lerp(col, blockCol, blockAmount * _GlitchIntensity);
                }

                fixed4 terminal = tex2D(_TerminalTex, i.uv);
                col.rgb = lerp(col.rgb, terminal.rgb, terminal.a * _TerminalOpacity);

                return col;
            }
            ENDCG
        }
    }
}
