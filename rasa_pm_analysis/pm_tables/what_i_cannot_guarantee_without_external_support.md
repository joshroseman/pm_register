# ### ⚠️ What I Cannot Guarantee Without External Support

| Function | Limitation |
|---|---|
| Long-term memory persistence | Once the session ends or threads expire, I cannot retrieve unsaved data unless it lives in canvas. |
| Autonomous parsing of large pasted blocks without loss | If data is pasted in a format with poor delimiters or missing field cues, I may misparse rows. |
| Lossless interpretation of malformed markdown | If the formatting is irregular (inconsistent pipes, missing headers), I may silently drop rows. |
| Rendering more than \~75--100 rows in a single canvas operation | This often causes markdown truncation or insertion failure unless chunked. |
