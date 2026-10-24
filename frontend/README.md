# Shibir Chatbot Frontend

A modern, highly responsive Next.js AI Chatbot interface built with Tailwind CSS, React Markdown, and Lucide icons.

## Features

- **Next.js App Router**: Optimized single-page application with `"use client"`.
- **Clean ChatGPT/Claude Aesthetics**: Minimalist, professional cards, soft shadows, rounded-2xl/3xl borders.
- **Dynamic CSS Variables**: Full support for light and dark themes using CSS variables (`var(--bg-primary)`, `var(--bg-card)`, `var(--text-primary)`, `var(--accent-solid)`).
- **Markdown Rendering**: Formatted bot answers (bold, bulleted lists, external links, inline code) using `react-markdown`.
- **Interactive Suggested Follow-up Questions**: Follow-up questions returned by the backend appear as clickable pill buttons that automatically dispatch new queries.
- **Auto-expanding Textarea**: Grows dynamically up to 160px height. `Enter` to submit, `Shift + Enter` for a new line.
- **Auto-scroll**: Automatically scrolls down smoothly as new messages stream or search loaders change.
- **Configurable Backend**: Easily switch between the live Render backend (`https://shibir-chatbot.onrender.com/api/chat/ask`) and local backend (`http://127.0.0.1:8000/api/chat/ask`).

## Quick Start

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.
