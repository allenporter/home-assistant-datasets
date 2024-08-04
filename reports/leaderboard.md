| Model | assist | assist-mini | intents|
| ----- | ----- | ----- | ----- |
| gemini-1.5-flash | 91.2% (+/- 3.2%) 2024.6.3 | 98.0% (+/- 2.0%) 2024.8.0dev | 0 |
| gpt-4o-mini | 90.0% (+/- 3.4%) 2024.8.0b | 98.0% (+/- 2.0%) 2024.8.0dev | 63.6% (+/- 3.7%) 2024.8.0b |
| gpt-4o | 87.5% (+/- 3.7%) 2024.6.3 | 0 | 81.2% (+/- 3.0%) 2024.6.3 |
| gpt-3.5 | 75.0% (+/- 4.8%) 2024.6.3 | 0 | 67.9% (+/- 3.6%) 2024.6.3 |
| functionary-small-v2.5 | 56.2% (+/- 5.5%) 2024.7.0 | 63.3% (+/- 6.9%) 2024.8.0dev | 37.6% (+/- 3.8%) 2024.6.3 |
| llama3.1 | 45.6% (+/- 5.6%) 2024.8.0b | 83.7% (+/- 5.3%) 2024.8.0b0 | 22.6% (+/- 3.3%) 2024.8.0b |
| home-llm | 45.0% (+/- 5.6%) 2024.6.3 | 34.7% (+/- 6.8%) 2024.8.0dev | 25.5% (+/- 3.4%) 2024.6.3 |
| assistant | 37.5% (+/- 5.4%) 2024.6.3 | 63.3% (+/- 6.9%) 2024.8.0dev | 98.8% (+/- 0.9%) 2024.6.3 |
| xlam-7b | 25.0% (+/- 4.8%) 2024.8.0b | 85.7% (+/- 5.0%) 2024.8.0b0 | 0 |
| llama3-groq-tool-use | 20.0% (+/- 4.5%) 2024.8.0b | 51.0% (+/- 7.1%) 2024.8.0b0 | 11.5% (+/- 2.5%) 2024.8.0b |
| mistral-v3 | 3.8% (+/- 2.1%) 2024.8.0b | 2.0% (+/- 2.0%) 2024.8.0dev | 10.3% (+/- 2.4%) 2024.8.0b |
| xlam-1b | 0 | 27.1% (+/- 6.4%) 2024.8.0b0 | 0 |

```mermaid
---
config:
    xyChart:
        width: 1600
        height: 500
        xAxis:
          labelFontSize: 10
          labelPadding: 10
    themeVariables:
        xyChart:
            titleColor: "#ff0000"
            plotColorPalette: "#4285f4, #ea4335, #fbbc04, #34a853, #ff6d01, #46bdc6, #1155cc"

---
xychart-beta
  title "assist"
  x-axis "Model" [assistant, functionary-small-v2.5, gemini-1.5-flash, gpt-3.5, gpt-4o, gpt-4o-mini, home-llm, llama3-groq-tool-use, llama3.1, mistral-v3, xlam-7b]
  y-axis "Score" 0 --> 100
  bar [37.5, 56.25, 91.25, 75.0, 87.5, 90.0, 45.0, 20.0, 45.57, 3.75, 25.0]
```


```mermaid
---
config:
    xyChart:
        width: 1600
        height: 500
        xAxis:
          labelFontSize: 10
          labelPadding: 10
    themeVariables:
        xyChart:
            titleColor: "#ff0000"
            plotColorPalette: "#4285f4, #ea4335, #fbbc04, #34a853, #ff6d01, #46bdc6, #1155cc"

---
xychart-beta
  title "assist-mini"
  x-axis "Model" [assistant, functionary-small-v2.5, gemini-1.5-flash, gpt-4o-mini, home-llm, llama3-groq-tool-use, llama3.1, mistral-v3, xlam-1b, xlam-7b]
  y-axis "Score" 0 --> 100
  bar [63.27, 63.27, 97.96, 97.96, 34.69, 51.02, 83.67, 2.04, 27.08, 85.71]
```


```mermaid
---
config:
    xyChart:
        width: 1600
        height: 500
        xAxis:
          labelFontSize: 10
          labelPadding: 10
    themeVariables:
        xyChart:
            titleColor: "#ff0000"
            plotColorPalette: "#4285f4, #ea4335, #fbbc04, #34a853, #ff6d01, #46bdc6, #1155cc"

---
xychart-beta
  title "intents"
  x-axis "Model" [assistant, functionary-small-v2.5, gpt-3.5, gpt-4o, gpt-4o-mini, home-llm, llama3-groq-tool-use, llama3.1, mistral-v3]
  y-axis "Score" 0 --> 100
  bar [98.79, 37.58, 67.88, 81.21, 63.64, 25.45, 11.52, 22.56, 10.3]
```
