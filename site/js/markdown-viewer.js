/**
 * Markdown Viewer Module
 * Enhances .md file links to display markdown content in a beautiful modal viewer
 * Works with Netlify static hosting - no server required
 */

const MarkdownViewer = {
  modal: null,

  // Initialize the markdown viewer
  init() {
    this.createModal();
    this.attachLinkHandlers();
  },

  // Create the modal viewer
  createModal() {
    const modal = document.createElement('div');
    modal.id = 'markdown-viewer-modal';
    modal.innerHTML = `
      <style>
        #markdown-viewer-modal {
          display: none;
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.85);
          z-index: 9999;
          overflow-y: auto;
          animation: fadeIn 0.3s ease;
        }

        #markdown-viewer-modal.active {
          display: block;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .markdown-modal-content {
          max-width: 900px;
          margin: 2rem auto;
          background: white;
          border-radius: 16px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
          animation: slideUp 0.4s ease;
          position: relative;
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(50px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .markdown-modal-header {
          background: linear-gradient(135deg, #14213d 0%, #1f4068 100%);
          color: white;
          padding: 1.5rem 2rem;
          border-radius: 16px 16px 0 0;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .markdown-modal-title {
          margin: 0;
          font-size: 1.5rem;
          font-weight: 600;
        }

        .markdown-close-btn {
          background: rgba(255, 255, 255, 0.2);
          border: none;
          color: white;
          width: 36px;
          height: 36px;
          border-radius: 50%;
          cursor: pointer;
          font-size: 1.5rem;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
        }

        .markdown-close-btn:hover {
          background: rgba(255, 255, 255, 0.3);
          transform: scale(1.1);
        }

        .markdown-modal-body {
          padding: 2rem;
          color: #333;
          line-height: 1.8;
          max-height: calc(100vh - 200px);
          overflow-y: auto;
        }

        .markdown-loading {
          text-align: center;
          padding: 3rem;
          color: #666;
        }

        .markdown-error {
          text-align: center;
          padding: 3rem;
          color: #d32f2f;
        }

        /* Markdown Content Styles */
        .markdown-content h1 {
          color: #14213d;
          font-size: 2.2rem;
          margin: 1.5rem 0 1rem;
          padding-bottom: 0.5rem;
          border-bottom: 3px solid #ffd166;
        }

        .markdown-content h2 {
          color: #1f4068;
          font-size: 1.8rem;
          margin: 1.5rem 0 1rem;
          padding-bottom: 0.3rem;
          border-bottom: 2px solid #e0e0e0;
        }

        .markdown-content h3 {
          color: #2d4a70;
          font-size: 1.4rem;
          margin: 1.2rem 0 0.8rem;
        }

        .markdown-content h4 {
          color: #3e5a82;
          font-size: 1.2rem;
          margin: 1rem 0 0.6rem;
        }

        .markdown-content p {
          margin: 0.8rem 0;
          line-height: 1.8;
        }

        .markdown-content ul,
        .markdown-content ol {
          margin: 0.8rem 0;
          padding-left: 2rem;
        }

        .markdown-content li {
          margin: 0.5rem 0;
        }

        .markdown-content code {
          background: #f5f5f5;
          border: 1px solid #e0e0e0;
          border-radius: 4px;
          padding: 0.2rem 0.4rem;
          font-family: 'Courier New', monospace;
          font-size: 0.9em;
        }

        .markdown-content pre {
          background: #f5f5f5;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 1rem;
          overflow-x: auto;
        }

        .markdown-content pre code {
          background: none;
          border: none;
          padding: 0;
        }

        .markdown-content blockquote {
          border-left: 4px solid #ffd166;
          background: #f9f9f9;
          padding: 1rem 1.5rem;
          margin: 1rem 0;
          font-style: italic;
        }

        .markdown-content strong {
          color: #14213d;
          font-weight: 600;
        }

        .markdown-content em {
          color: #1f4068;
        }

        .markdown-content hr {
          border: none;
          border-top: 2px solid #e0e0e0;
          margin: 2rem 0;
        }

        .markdown-content a {
          color: #1f4068;
          text-decoration: none;
          border-bottom: 1px solid #1f4068;
          transition: all 0.2s ease;
        }

        .markdown-content a:hover {
          color: #ffd166;
          border-bottom-color: #ffd166;
        }

        .markdown-content table {
          width: 100%;
          border-collapse: collapse;
          margin: 1rem 0;
        }

        .markdown-content th,
        .markdown-content td {
          border: 1px solid #e0e0e0;
          padding: 0.75rem;
          text-align: left;
        }

        .markdown-content th {
          background: #14213d;
          color: white;
          font-weight: 600;
        }

        .markdown-content tr:nth-child(even) {
          background: #f9f9f9;
        }

        @media (max-width: 768px) {
          .markdown-modal-content {
            margin: 1rem;
            border-radius: 12px;
          }

          .markdown-modal-header {
            padding: 1rem;
            border-radius: 12px 12px 0 0;
          }

          .markdown-modal-title {
            font-size: 1.2rem;
          }

          .markdown-modal-body {
            padding: 1rem;
          }

          .markdown-content h1 {
            font-size: 1.8rem;
          }

          .markdown-content h2 {
            font-size: 1.5rem;
          }
        }

        @media print {
          #markdown-viewer-modal {
            display: none;
          }
        }
      </style>

      <div class="markdown-modal-content">
        <div class="markdown-modal-header">
          <h2 class="markdown-modal-title">Loading...</h2>
          <button class="markdown-close-btn" onclick="MarkdownViewer.close()">×</button>
        </div>
        <div class="markdown-modal-body">
          <div class="markdown-loading">Loading content...</div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    this.modal = modal;

    // Close on background click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        this.close();
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.classList.contains('active')) {
        this.close();
      }
    });
  },

  // Attach click handlers to markdown links
  attachLinkHandlers() {
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href$=".md"]');
      if (link) {
        e.preventDefault();
        this.open(link.href, link.textContent || 'Document');
      }
    });
  },

  // Open modal and load markdown content
  async open(url, title) {
    this.modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    const titleEl = this.modal.querySelector('.markdown-modal-title');
    const bodyEl = this.modal.querySelector('.markdown-modal-body');

    titleEl.textContent = title;
    bodyEl.innerHTML = '<div class="markdown-loading">Loading content...</div>';

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const markdown = await response.text();
      const html = this.parseMarkdown(markdown);

      bodyEl.innerHTML = `<div class="markdown-content">${html}</div>`;
    } catch (error) {
      console.error('Error loading markdown:', error);
      bodyEl.innerHTML = `
        <div class="markdown-error">
          <h3>Error Loading Content</h3>
          <p>Could not load the markdown file. Please try again or contact support.</p>
          <p><small>Error: ${error.message}</small></p>
        </div>
      `;
    }
  },

  // Close modal
  close() {
    this.modal.classList.remove('active');
    document.body.style.overflow = '';
  },

  // Simple markdown parser
  parseMarkdown(markdown) {
    let html = markdown;

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
    html = html.replace(/__(.*?)__/gim, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.*?)\*/gim, '<em>$1</em>');
    html = html.replace(/_(.*?)_/gim, '<em>$1</em>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank">$1</a>');

    // Code blocks
    html = html.replace(/```([^`]+)```/gim, '<pre><code>$1</code></pre>');

    // Inline code
    html = html.replace(/`([^`]+)`/gim, '<code>$1</code>');

    // Blockquotes
    html = html.replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>');

    // Horizontal rules
    html = html.replace(/^---$/gim, '<hr>');
    html = html.replace(/^\*\*\*$/gim, '<hr>');

    // Unordered lists
    html = html.replace(/^\* (.*$)/gim, '<li>$1</li>');
    html = html.replace(/^- (.*$)/gim, '<li>$1</li>');

    // Ordered lists
    html = html.replace(/^\d+\. (.*$)/gim, '<li>$1</li>');

    // Wrap consecutive list items
    html = html.replace(/(<li>.*<\/li>\n?)+/gim, '<ul>$&</ul>');

    // Paragraphs (lines not already wrapped in tags)
    const lines = html.split('\n');
    const processedLines = lines.map(line => {
      line = line.trim();
      if (line && !line.match(/^<[^>]+>/)) {
        return `<p>${line}</p>`;
      }
      return line;
    });

    html = processedLines.join('\n');

    // Clean up extra whitespace
    html = html.replace(/\n\s*\n/g, '\n');

    return html;
  }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => MarkdownViewer.init());
} else {
  MarkdownViewer.init();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = MarkdownViewer;
}
