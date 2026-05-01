# Throwaway scripts that weren't

* [markdown-to-confluence](./markdown-to-confluence.py) - Useful to convert your `/plan` / `/research` artifacts into Confluence pages.

  Usage:
  ```bash
     # Basic conversion (Ref N markers + reference table)
     python markdown-to-confluence.py input.md -o output.md

     # With footnotes converted to GitHub hyperlinks
     python markdown-to-confluence.py input.md -o output.md \
       --base-url "https://github.com/org/repo/blob/SHA"
     # To stdout
     python markdown-to-confluence.py input.md
    ```
  Transformations applied:

     - Arrows (→, ←, ⇒) to ASCII equivalents
     - Em dashes (—) to --
     - Horizontal rules removed
     - Tree-drawing characters (├──, └──, │) to indented lists
     - Footnotes to inline refs (or hyperlinks with --base-url)
     - ToC anchors adjusted for Confluence
     - Backticks stripped from hyperlink-adjacent text
     - Non-ASCII characters cleaned up
     - Excess blank lines collapsed
