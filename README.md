# LLM INDEX

This site collects a majority of large model platforms available in the market, such as ChatGPT, as well as efficiency tools driven by large models, like the programming assistant Cursor. It also includes websites that utilize AI for creative tasks, such as music, video, and image generation.

![/images/workflow.png](/images/workflow.png)

The workflow demonstrates how the site updates its data and the overall triggering process after updates. The pages are deployed on Cloudflare Pages, and the data is hosted on Feishu's Bitable. When the repository is updated via `git push` or triggered through a webhook, scripts automatically fetch the latest data from Feishu Bitable and rebuild the web pages.