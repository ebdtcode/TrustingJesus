# Trusting Jesus - Site Organization Guide
## Complete Structure for Spiritual Growth Resources

---

## 📁 Site Organization Structure

### **Weekly Content Organization**
All content is organized by week/date for easy access and chronological browsing:

```
📁 prayer_trusting_Jesus/
├── 📄 spiritual_growth_dashboard.html (NEW - Main Hub)
├── 📁 2025/
│   └── 📁 September/
│       └── 📁 Week_3_Sept_21/
│           ├── 📄 Gospel_of_Grace_Sermon.md
│           ├── 📄 Gospel_of_Grace_Presentation.html
│           ├── 📄 Gospel_of_Grace_Prayer_Points.md
│           └── 📄 Gospel_of_Grace_Summary.md
├── 📁 presentations/
│   ├── 📄 Gospel_of_Grace_Presentation.html (51 slides)
│   └── 📄 Have_I_Not_Called_You_Presentation.html
├── 📁 prayer_points/
│   └── 📁 2025/
│       └── 📄 Week-2025-09-21_Gospel_of_Grace.md
├── 📁 transcripts/
│   └── 📁 sermon/
│       └── 📄 Sermon_Sep_21_2025_Gospel_of_grace.md
├── 📁 templates/
│   └── 📄 WEEKLY_PRESENTATION_TEMPLATE.html (NEW)
└── 📁 site/
    ├── 📄 index.html
    ├── 📄 prayer.html
    ├── 📄 sermons.html
    ├── 📄 presentations.html
    └── 📁 data/
        ├── 📄 weekly_content.json (NEW)
        ├── 📄 prayer_points.json
        ├── 📄 presentations.json
        └── 📄 sermons.json
```

---

## 🎯 Content Access Points

### **1. Main Dashboard**
📍 **Location**: `spiritual_growth_dashboard.html`
- Central hub for all spiritual growth resources
- Weekly content spotlight
- Quick access cards for all content types
- Search and filter functionality
- Timeline view of all content

### **2. Weekly Content View**
Each week contains:
- **Sermon**: Full transcript with speaker attribution
- **Presentation**: 51-slide deck with navigation sidebar
- **Prayer Points**: 8 focused prayer topics with scriptures
- **Summary**: Key takeaways and action steps

### **3. Content Categories**

#### **Sermons**
- Organized by date
- Speaker: Bishop J. Darlingston (Gospel of Grace)
- Full transcripts available
- Linked to presentations and prayer points

#### **Presentations**
- Consistent styling (#03396C background, #FF8D21 accent)
- Left sidebar navigation (PowerPoint-style)
- Prayer points summary slide (Slide 2)
- Mobile responsive design
- Print-friendly for PDFs

#### **Prayer Points**
- Weekly collections (8 points per week)
- Scripture-based focus
- Action steps included
- Organized by date/week

---

## 🎨 Consistent Design Elements

### **Color Scheme**
- **Primary**: #03396C (Deep Blue)
- **Accent**: #FF8D21 (Bright Orange)
- **Highlight**: #FFD700 (Gold)
- **Text**: White on dark, dark on light

### **Typography**
- **Headings**: Segoe UI, system fonts
- **H1**: 4rem (64px)
- **H2**: 3rem (48px)
- **Body**: 1.8rem (28px)
- **Mobile**: Scaled down 20%

### **Navigation Features**
- Sidebar with thumbnails
- Keyboard shortcuts (arrows, space, Home/End)
- Touch/swipe on mobile
- Progress bar
- Slide counter

---

## 📅 Current Content Library

### **September 2025**

#### **Week 3 (Sept 21): The Gospel of Grace**
- **Speaker**: Bishop J. Darlingston
- **Scripture**: Romans 5:1-2
- **Theme**: Peace with God Through Jesus Christ
- **Resources**:
  - 51-slide presentation with sidebar navigation
  - 8 prayer points (Peace Child, Legal Standing, etc.)
  - Full sermon transcript
  - Comprehensive summary

#### **Previous Content**
- **"Have I Not Called You"** presentation
  - Standalone presentation file
  - Available in presentations folder

---

## 🔧 How to Add New Weekly Content

### **Step 1: Use the Template**
1. Copy `WEEKLY_PRESENTATION_TEMPLATE.html`
2. Replace all [BRACKETED] placeholders
3. Add sermon content slides
4. Update slide titles array in JavaScript

### **Step 2: Create Prayer Points**
1. Use the format from `Week-2025-09-21_Gospel_of_Grace.md`
2. Include 8 scripture-based points
3. Add action steps
4. Save in `prayer_points/[YEAR]/Week-[DATE]_[TITLE].md`

### **Step 3: Update Data Files**
1. Add entry to `weekly_content.json`
2. Update `prayer_points.json`
3. Update `presentations.json`
4. Update `sermons.json`

### **Step 4: Link in Dashboard**
1. Dashboard automatically reads from JSON files
2. Content appears in timeline view
3. Search functionality includes new content

---

## 🔍 Search & Discovery

### **By Date/Week**
- Timeline view in dashboard
- Weekly folders in file structure
- Date-stamped filenames

### **By Type**
- Sermons section
- Presentations gallery
- Prayer points archive

### **By Speaker**
- Bishop J. Darlingston
- Other speakers as added

### **By Scripture**
- Tagged in JSON metadata
- Searchable in dashboard

---

## 📱 Responsive Design

### **Desktop (1200px+)**
- Full sidebar navigation
- Multi-column layouts
- Large typography

### **Tablet (768px-1199px)**
- Collapsible sidebar
- Adjusted typography
- Touch-friendly controls

### **Mobile (<768px)**
- Overlay sidebar
- Single column
- Swipe navigation
- Optimized font sizes

---

## ✅ Quality Checklist for New Content

- [ ] Uses consistent color scheme
- [ ] Includes prayer points summary (Slide 2)
- [ ] Has sidebar navigation
- [ ] Mobile responsive
- [ ] Print-friendly CSS
- [ ] Speaker attribution included
- [ ] Date clearly marked
- [ ] Scripture references formatted
- [ ] Linked in JSON data files
- [ ] Added to dashboard timeline

---

## 📈 Benefits of This Organization

1. **Easy Discovery**: Content organized by week/date
2. **Consistent Experience**: Same design across all presentations
3. **Multiple Access Points**: Dashboard, direct links, category pages
4. **Search Friendly**: Metadata enables searching
5. **Mobile Ready**: Works on all devices
6. **Print Capable**: Clean PDFs for handouts
7. **Scalable**: Easy to add new content weekly
8. **Professional**: Church-quality presentation

---

## 🚀 Quick Start for Users

1. **Open Dashboard**: `spiritual_growth_dashboard.html`
2. **Browse by Week**: See timeline of all content
3. **Click to Access**: Direct links to all resources
4. **Use Navigation**: Sidebar for presentations
5. **Print if Needed**: Browser print to PDF

---

## 📝 Notes

- All paths use relative links for portability
- JSON files enable dynamic content loading
- Template ensures consistency week after week
- Dashboard provides unified access point
- Organization supports growth over time

---

*Last Updated: September 2025*
*Organization System Version: 2.0*