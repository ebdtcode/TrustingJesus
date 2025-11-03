# Health Education Center

A comprehensive web resource providing evidence-based medical information on thyroid health, TSH levels, and natural wellness approaches.

## 🌐 Live Site

Deploy this site to Netlify, Vercel, or any static hosting service.

## 📁 Site Structure

```
health/site/
├── index.html                 # Main dashboard/homepage
├── presentations.html         # Presentations listing page
├── transcripts.html          # Transcripts listing page
├── translations.html         # Translations listing page
├── netlify.toml             # Netlify deployment configuration
├── assets/
│   ├── css/
│   │   ├── site.css         # Dashboard & listing page styles
│   │   └── slides.css       # Presentation slides styles
│   └── js/
│       └── slides.js        # Presentation navigation logic
├── presentations/
│   ├── Understanding_High_TSH_Thyroid_Health.html
│   └── Natural_Ways_to_Lower_TSH.html
├── transcripts/
│   ├── E84wbXX5-7A_transcript.txt
│   ├── E84wbXX5-7A.srt
│   └── E84wbXX5-7A.mp3
├── translations/
│   ├── E84wbXX5-7A_translation_en.txt
│   └── Natural_Ways_to_Lower_TSH_Research.txt
└── data/
    └── (Future: JSON files for dynamic content)
```

## 🎯 Features

### Presentations
- **Professional slide decks** with medical theme (blue gradient, yellow accents)
- **Sidebar navigation** for quick slide access
- **Keyboard shortcuts** (arrows, space, home, end, page up/down)
- **Touch/swipe support** for mobile devices
- **Print-friendly** CSS for PDF export
- **Mobile responsive** design

### Content
- **18-slide presentation** on Understanding High TSH Levels
- **38-slide presentation** on Natural Ways to Lower TSH
- **Video transcripts** with timestamps
- **English translations** of medical content
- **Research compilations** from multiple expert sources

### Design
- Consistent medical education theme
- Accessibility-focused (WCAG AA)
- Fast loading with external CSS/JS
- Security headers via Netlify
- Proper caching strategy

## 🚀 Deployment

### Netlify (Recommended)

1. **Connect Repository:**
   ```bash
   cd /path/to/media/health/site
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy to Netlify:**
   - Log in to [Netlify](https://netlify.com)
   - Click "Add new site" → "Import an existing project"
   - Connect your Git repository
   - Build settings (auto-detected from netlify.toml):
     - Build command: (none needed)
     - Publish directory: `.` (root)
   - Click "Deploy"

3. **Custom Domain (Optional):**
   - Go to Site settings → Domain management
   - Add your custom domain
   - Update DNS records as instructed

### Other Hosting Options

**Vercel:**
```bash
npm install -g vercel
cd /path/to/media/health/site
vercel
```

**GitHub Pages:**
```bash
# Push to GitHub, then enable Pages in repo settings
git push origin main
```

**Static File Server (Local Testing):**
```bash
cd /path/to/media/health/site
python -m http.server 8000
# Visit http://localhost:8000
```

## 📊 Presentations Usage

### Keyboard Navigation
- **Arrow Keys** or **Space** - Navigate slides
- **Home** - Jump to first slide
- **End** - Jump to last slide
- **Page Up/Down** - Jump 10 slides
- **Escape** - (Future: Exit fullscreen)

### Mobile Navigation
- **Swipe left/right** - Navigate slides
- **Tap hamburger menu (☰)** - Open/close sidebar
- **Tap slide titles** - Jump directly to slide

### Print to PDF
1. Open any presentation
2. Press `Ctrl+P` (Windows) or `Cmd+P` (Mac)
3. Select "Save as PDF"
4. All slides will be included with proper formatting

## 🎨 Customization

### Update Branding
Edit `assets/css/site.css` and `assets/css/slides.css`:
```css
:root {
  --primary-blue: #14213d;      /* Main background */
  --accent-yellow: #ffd166;     /* Accent color */
  /* ... other variables ... */
}
```

### Add New Presentations
1. Create HTML file in `presentations/` folder
2. Include external CSS: `<link rel="stylesheet" href="../assets/css/slides.css">`
3. Include external JS: `<script src="../assets/js/slides.js"></script>`
4. Initialize with slide titles:
   ```html
   <script>
     const slideTitles = ['Slide 1', 'Slide 2', ...];
     const sectionBreaks = [3, 6, 9];
     initPresentation(slideTitles, sectionBreaks);
   </script>
   ```
5. Update `presentations.html` to list the new presentation

## 📝 Content Sources

### Medical Experts
- **Dr. B. K. Roy** - MBBS, MD, DM (Endocrinology)
- **Dr. Izabella Wentz, PharmD** - Thyroid Pharmacist
- **Dr. Michael Ruscio, DC** - Integrative Medicine

### Research
- Peer-reviewed clinical studies (2003-2025)
- Patient outcome surveys and clinical data
- Evidence-based natural health approaches

## ⚠️ Medical Disclaimer

This site provides educational information only and is **not a substitute for professional medical advice, diagnosis, or treatment**. Always consult with qualified healthcare providers before making any changes to your health regimen.

## 📄 License

Content is provided for educational purposes. Consult with medical professionals for personal health decisions.

## 🔧 Technical Requirements

- **No build process** required
- **No dependencies** (pure HTML/CSS/JS)
- Works on all modern browsers
- Mobile responsive
- Accessible (WCAG AA compliant)

## 🆘 Support

For questions or issues:
1. Check the presentation navigation by pressing `H` for help (future feature)
2. Ensure JavaScript is enabled for full functionality
3. Use latest version of modern browsers (Chrome, Firefox, Safari, Edge)

## 📚 Future Enhancements

- [ ] Add JSON data files for dynamic content loading
- [ ] Create more health topic presentations
- [ ] Add search functionality
- [ ] Implement user progress tracking
- [ ] Add video embedding for original sources
- [ ] Multi-language support beyond English
- [ ] Interactive quizzes and knowledge checks
- [ ] Printable summary PDFs

---

**Last Updated:** October 2025
**Version:** 1.0.0
