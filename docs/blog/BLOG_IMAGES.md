# Blog Images — Medium Upload Guide

Upload these images in order when publishing on Medium:

| # | File                                      | Section                | Alt text                                      |
|---|-------------------------------------------|------------------------|-----------------------------------------------|
| 1 | `docs/images/dashboard.png`               | After title (hero)     | Dashboard showing live health scores          |
| 2 | `docs/images/pipeline-diagram.png`        | How It Works section   | Pipeline diagram — T0 through T5 flow         |
| 3 | `docs/images/self-attack-output.png`      | Results section        | Health scores table for top 5 Mantle contracts|
| 4 | *(no file — Cloudflare blocks automated screenshots)* | On-chain proof section | On-chain alert transaction on Mantlescan |

### Notes

- **Image 4 fallback:** BLOG_POST.md uses a styled Mantlescan link instead of an image. To add a screenshot manually:
  1. Open <https://mantlescan.xyz/tx/0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c> in a browser
  2. Take a screenshot of the transaction details area (1280×800 recommended)
  3. Save as `docs/images/mantlescan-alert-tx.png`
  4. Replace the blockquote in BLOG_POST.md with:
     ```markdown
     ![On-chain alert transaction on Mantlescan](../images/mantlescan-alert-tx.png)

     *[View transaction on Mantlescan →](https://mantlescan.xyz/tx/0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c)*
     ```

- Medium tip: drag images into the editor at the corresponding placeholder positions.
- All images are PNG format (Medium doesn't support SVG).
