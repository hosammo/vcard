# VIRTUAL BUSINESS CARD - FEATURE IMPLEMENTATION ROADMAP
## Complete Feature List — Live Status Reference

> **Legend:**
> - `[x]` = Implemented & working
> - `[~]` = Partially implemented
> - `[ ]` = Not yet built

---

## CURRENT BUILD STATUS

| Sprint | Status | What was delivered |
|---|---|---|
| **Phase 1** — Core Auth & Cards | ✅ Complete | Register, login, dashboard, create/edit/delete card, public card view |
| **Phase 2** — Enhanced Cards | ✅ Complete | Phone numbers, image uploads, social links, custom links, colors, QR code, vCard |
| **Phase 3** — Card Management | ✅ Complete | My Cards, search, filter, sort, bulk ops, duplicate, archive |
| **Phase 4** — Analytics | ✅ Complete | View/download tracking, charts (line/doughnut/pie), referrers, date ranges, CSV export |
| **Phase 5** — Team Management | ✅ Complete | Organizations, invites (with email security), roles, multi-tenant |
| **Sprint A** — Account Settings | ✅ Complete | 5-tab settings page, UserSettings model, ActivityLog model, delete account |
| **Sprint B** — Card Polish | 🔜 Next | Sharing modal, password toggle on login, terms checkbox, type filter, stats bar |
| **Sprint C** — Analytics+ | 🔜 Planned | Top locations table, recent activity table, CSV export on analytics page |
| **Sprint D** — Landing Polish | 🔜 Planned | Animated hero, feature cards, how-it-works, footer links |
| **Billing** | 🟡 Simulated | Plan tiers, upgrade UI, billing page — no real Stripe yet |
| **Advanced** | ❌ Future | 2FA, social login, email verification, custom domains, mobile app |

---

## 1. LANDING PAGE FEATURES

### 1.1 Navigation & Header
- [~] Sticky navigation bar with logo *(basic version exists)*
- [ ] Menu items (Features, Pricing, About, Contact)
- [x] "Sign In" button
- [x] "Get Started" / "Create Account" CTA button
- [~] Mobile responsive hamburger menu *(sidebar has mobile toggle)*
- [ ] Smooth scroll navigation to sections

### 1.2 Hero Section
- [~] Animated gradient background *(static gradient exists)*
- [x] Main headline with CTA text
- [x] Subheadline description
- [x] Two CTA buttons (Sign In, Create Account)
- [ ] Animated background pattern/dots

### 1.3 Features Section
- [~] 6 Feature cards with icons *(3 cards with icons exist)*
- [~] Feature descriptions *(basic descriptions present)*
- [ ] Icon animations on hover

### 1.4 How It Works Section
- [ ] 3-step process visualization
- [ ] Numbered step indicators
- [ ] Step descriptions

### 1.5 Pricing Section
- [x] 3 pricing tiers (Free / Pro / Business)
- [x] Feature comparison lists
- [x] "Choose Plan" buttons
- [x] "Most Popular" badge for Pro plan
- [ ] Pricing card hover effects

### 1.6 Final CTA Section
- [ ] Gradient background CTA banner
- [ ] Call-to-action headline
- [ ] "Start Your Free Card" button

### 1.7 Footer
- [~] Logo and company tagline *(partial)*
- [ ] Product links (Features, Pricing, Templates)
- [ ] Company links (About, Blog, Careers, Contact)
- [ ] Legal links (Privacy Policy, Terms of Service)
- [ ] Social media icons (Twitter, LinkedIn, Facebook, Instagram)
- [x] Copyright notice

---

## 2. LOGIN/REGISTRATION PAGES

### 2.1 Login Page
- [x] Email input field with icon
- [x] Password input field with icon
- [ ] Password visibility toggle (eye icon) *(Sprint B)*
- [ ] "Remember Me" checkbox
- [x] "Forgot Password?" link
- [x] Login button
- [ ] Social login buttons (Google, LinkedIn) *(Advanced)*
- [x] "Sign Up" link for new users
- [x] "Back to Home" link
- [x] Error message display area
- [x] Gradient animated background

### 2.2 Registration Page
- [x] First name field
- [x] Last name field
- [x] Email field (locked to invite email when coming from invite)
- [x] Password field with strength indicator
- [x] Confirm password field
- [ ] Terms & conditions checkbox *(Sprint B)*
- [x] Sign up button
- [ ] Social registration options *(Advanced)*
- [x] "Already have account?" login link
- [x] Auto-login after registration
- [x] Redirect to invite page after register (via ?next=)

### 2.3 Forgot Password Flow *(fully implemented)*
- [x] Forgot password page (email entry)
- [x] Password reset email (console backend in dev)
- [x] Reset password form (set new password)
- [x] Password reset confirmation page

---

## 3. DASHBOARD FEATURES

### 3.1 Sidebar Navigation
- [x] Fixed sidebar (260px width)
- [x] Logo with icon
- [x] Menu items with icons:
  - [x] Dashboard
  - [x] Create Card
  - [x] Leads Inbox (with unread badge)
  - [x] Team (Business plan only)
  - [x] My Profile
  - [x] Upgrade Plan
  - [x] Billing
  - [ ] Help & Support
- [x] Active state highlighting
- [x] Collapsible sidebar for mobile (hamburger overlay)
- [x] User avatar (initials)
- [x] User name display
- [x] User email display
- [x] Plan badge (Free / Pro / Business)
- [x] Organisation name display

### 3.2 User Profile Dropdown
- [ ] Clickable profile trigger with dropdown
- [ ] Dropdown menu (My Profile, Billing, Help, Sign Out)
- [ ] Slide-up animation
- [ ] Click outside to close
- [ ] Chevron icon rotation

### 3.3 Top Bar
- [x] Page title / breadcrumbs
- [ ] Notification bell with badge counter
- [x] Mobile menu toggle button

### 3.4 Statistics Section
- [x] Total Cards stat card
- [x] Total Views stat card
- [x] Total Downloads stat card
- [x] Conversion Rate stat card
- [x] Gradient icon backgrounds
- [~] Trend indicators *(basic percentage shown)*
- [x] Hover lift animations

### 3.5 Business Cards Display — Grid View
- [x] 3-column responsive grid
- [x] Gradient banner
- [x] Profile avatar / initials fallback
- [x] Full name
- [x] Job title
- [x] Status badge (Active / Inactive)
- [x] View count
- [x] Download count
- [x] View / Edit / Options action buttons
- [x] Hover effects (lift and shadow)

### 3.5 Business Cards Display — List View
- [x] Horizontal card layout
- [x] Avatar on left
- [x] Card info in center
- [x] Stats inline (Views, Downloads, Created date)
- [x] Action buttons on right
- [x] Responsive (stacks on mobile)

### 3.6 Card Options Dropdown
- [x] Three-dot menu button
- [x] View Analytics
- [x] Download QR Code
- [x] Share Card *(basic — Sprint B adds modal)*
- [x] Duplicate
- [x] Archive
- [x] Delete Card (danger colour)
- [x] Click outside to close
- [x] Smooth animation

### 3.7 View Switcher
- [x] Toggle between grid/list view
- [x] Active state highlighting
- [x] Smooth transitions

### 3.8 Empty State (Onboarding)
- [x] Rocket icon display
- [x] "No cards yet" message
- [x] 3-step visual onboarding guide (Create → Share → Track)
- [x] "Create Your First Card" CTA button
- [x] Free plan upgrade nudge

---

## 4. MY CARDS PAGE FEATURES

### 4.1 Stats Summary Bar
- [~] 3 mini stat cards *(stats are on dashboard; My Cards has simpler header)*
- [ ] Dedicated compact stats bar on My Cards *(Sprint B)*

### 4.2 Advanced Filter Bar
- [x] Search box with real-time filtering
- [x] Search by name, title, or company
- [x] Status filter dropdown (All / Active / Inactive)
- [ ] Type filter dropdown (All / Personal / Business / Freelance / Academic / Creative) *(Sprint B)*
- [x] Sort dropdown (Recent / Oldest / Most Views / Name A-Z)
- [x] View toggle buttons (Grid / List)

### 4.3 Bulk Actions Bar
- [x] Master "Select All" checkbox
- [x] Individual card checkboxes
- [x] Selected count display
- [x] Bulk activate selected
- [x] Bulk deactivate selected
- [ ] Bulk export selected *(planned)*
- [x] Bulk delete selected
- [x] Auto-show/hide based on selection
- [x] Indeterminate checkbox state

### 4.4 Cards Display
- [x] Same grid view as Dashboard
- [x] Same list view as Dashboard
- [x] Selection checkboxes on each card
- [x] All card options (view, edit, options dropdown)
- [x] Filtering functionality
- [x] Sorting functionality

---

## 5. CREATE / EDIT CARD PAGE FEATURES

### 5.1 Basic Information Section
- [x] Profile type dropdown (Personal / Business / Freelance / Academic / Creative)
- [x] First name input (required)
- [x] Last name input (required)
- [x] Job title input
- [x] Company input
- [x] Custom URL slug input with pattern validation
- [x] Auto-generation of slug
- [x] Bio textarea (500 char max with counter)
- [x] Skills / Services textarea

### 5.2 Contact Information Section
- [x] Email address input
- [x] Website URL input
- [x] Address textarea

### 5.3 Phone Numbers Section (Multiple)
- [x] Phone number list container
- [x] Add phone number button
- [x] Remove phone number button
- [x] Type dropdown (Mobile / Work / Home / Fax / Other)
- [x] Country code dropdown with flags
- [x] Number input field
- [x] Primary checkbox (only one can be primary)
- [x] WhatsApp available checkbox
- [x] Dynamic add/remove functionality

### 5.4 Social Media Section
- [x] LinkedIn URL input
- [x] Twitter / X URL input
- [x] Instagram URL input
- [x] Facebook URL input
- [x] Portfolio URL input

### 5.5 Custom Links Section
- [x] Custom Link 1 — Title + URL
- [x] Custom Link 2 — Title + URL

### 5.6 Images Section
- [x] Profile photo upload (click or drag & drop)
- [x] File type validation (PNG, JPG)
- [x] Image preview
- [x] Company logo upload
- [x] Banner image upload
- [x] Banner text overlay input

### 5.7 Customization Section
- [x] Background colour picker
- [x] Accent colour picker
- [x] Text colour picker
- [x] Live colour preview swatches

### 5.8 Live Preview Panel
- [x] Sticky preview container
- [x] Real-time preview updates as user types
- [x] Banner with custom gradient colours
- [x] Banner text overlay
- [x] Profile avatar / initials
- [x] Full name, job title, company, bio
- [x] Email, website
- [x] Social media icons
- [x] Custom links preview
- [ ] Desktop / Mobile view switcher *(not yet)*

### 5.9 Form Actions
- [x] Save / Create button
- [x] Cancel button
- [x] Form validation
- [x] Success / error messages

---

## 6. PROFILE / ACCOUNT SETTINGS PAGE FEATURES

### 6.1 Settings Navigation
- [x] 5-tab vertical pill nav (Profile / Security / Notifications / Privacy / Activity)
- [x] Active state highlighting
- [x] Tab switching — client-side with URL sync (?tab=)
- [x] Tab persists after form submit redirect

### 6.2 Profile Tab
- [x] Large avatar with initials
- [ ] Avatar photo upload / edit
- [x] User full name display
- [x] User email display
- [x] Plan badge (Free / Pro / Business)
- [x] Organisation name
- [x] First name / last name edit form
- [x] Email edit (with uniqueness check)
- [ ] Phone number field
- [ ] Bio / location fields
- [x] Read-only username display
- [x] Save changes button
- [x] Account Info card (member since, last login, workspace, role)

### 6.3 Security Tab
- [x] Current password input
- [x] New password input with strength bar (5 levels)
- [x] Confirm password with live match indicator
- [x] Password show/hide eye toggle on all fields
- [x] Update password button (keeps user logged in)
- [ ] Two-Factor Authentication toggle *(Advanced)*
- [x] **Danger Zone — Delete Account**
  - [x] Red warning section
  - [x] Full consequences bullet list
  - [x] Modal with typed "DELETE" confirmation
  - [x] Button disabled until "DELETE" typed exactly
  - [x] Logs activity, logs out, deletes user + cascade

### 6.4 Billing
- [x] Separate billing page (/billing/)
- [x] Current plan display
- [x] Upgrade plan page (/upgrade/)
- [~] Simulated payment flow
- [ ] Real Stripe integration *(Future)*
- [ ] Payment method display / update *(Future)*
- [ ] Billing history table *(Future)*
- [ ] Invoice download *(Future)*

### 6.5 Notifications Tab
- [x] Email Notifications toggle
- [x] Card View Alerts toggle
- [x] Contact Download Notifications toggle
- [x] Marketing Emails toggle
- [x] Weekly Reports toggle
- [x] Billing Updates toggle
- [x] Auto-save on toggle (fetch, no page reload)
- [x] "Preferences saved" inline confirmation
- [x] Persisted in UserSettings model (DB)

### 6.6 Privacy Tab
- [x] Public Profile toggle
- [x] Search Engine Indexing toggle
- [x] Analytics Tracking toggle
- [x] Data Sharing toggle
- [x] Auto-save on toggle (fetch, no page reload)
- [x] "Privacy settings saved" inline confirmation
- [x] Persisted in UserSettings model (DB)
- [ ] Data export (button present, marked "Coming soon")

### 6.7 Activity Tab
- [x] Recent activity timeline (last 20 events)
- [x] Colour-coded icons per action type
- [x] Login events (with IP address)
- [x] Password changed events
- [x] Profile updated events
- [x] Settings changed events
- [x] Relative timestamp ("2 minutes ago")
- [ ] Activity log pagination *(shows last 20 only)*
- [ ] Card created / updated / deleted events *(view only — not yet logged from card views)*

---

## 7. ANALYTICS PAGE FEATURES

### 7.1 Top Controls
- [x] Card selector dropdown (All cards + individual)
- [x] Date range: 7 Days / 30 Days / 90 Days / 1 Year / All Time
- [x] CSV export (/statistics/<id>/export/)
- [ ] PDF export *(planned)*

### 7.2 Key Metrics Cards
- [x] Total Views — count + percentage change vs previous period
- [x] Contact Downloads — count + percentage change
- [x] Conversion Rate — percentage + change
- [ ] Average Time on Card *(requires JS beacon — planned)*
- [x] Trend indicators (up/down arrows with colour)
- [x] Colour-coded icons

### 7.3 Views Over Time Chart
- [x] Line chart (Chart.js)
- [x] Bar chart toggle option
- [x] Gradient fill under line
- [x] Interactive tooltips
- [x] Responsive canvas
- [x] Date labels on X-axis

### 7.4 Traffic Sources Chart
- [x] Doughnut chart (Chart.js)
- [x] QR Code / LinkedIn / Direct / Twitter / Facebook / Other breakdown
- [x] Colour-coded segments
- [x] Interactive legend
- [x] Percentage tooltips

### 7.5 Device Breakdown Chart
- [x] Pie chart (Chart.js)
- [x] Mobile / Desktop / Tablet categories
- [x] Colour-coded segments
- [x] Interactive legend

### 7.6 Top Referrers Section
- [x] Progress bars per referrer source
- [x] Icon per referrer type
- [x] Count + percentage display
- [x] Animated progress bars

### 7.7 Top Locations Table
- [ ] Country column with flag emoji *(Sprint C)*
- [ ] City column *(Sprint C)*
- [ ] Views + downloads count *(Sprint C)*
- [ ] Percentage progress bar *(Sprint C)*

### 7.8 Recent Activity Table (on analytics page)
- [ ] Date & Time column *(Sprint C)*
- [ ] Action badges (View / Download) *(Sprint C)*
- [ ] Location (City, Country) *(Sprint C)*
- [ ] Device badge *(Sprint C)*
- [ ] Referrer column *(Sprint C)*

### 7.9 Export Functionality
- [x] CSV export (per-card, date range aware)
- [ ] PDF export *(planned)*
- [ ] Excel export *(planned)*

---

## 8. TEAM MANAGEMENT FEATURES *(not in original roadmap — fully built)*

### 8.1 Organisation Model
- [x] Multi-tenant Organisation with UUID primary key
- [x] Plan tiers: Free / Pro / Business
- [x] Card limit, seat limit, analytics gate per plan
- [x] Auto-created on user registration (owner role)
- [x] Stripe customer / subscription ID fields (ready for integration)

### 8.2 Organisation Members
- [x] Roles: Owner / Admin / Editor / Viewer
- [x] Permission shortcuts (can_edit, can_manage_members, can_manage_billing)
- [x] Invite via email with secure UUID token
- [x] Invite email validation (server-side: wrong email = rejected)
- [x] JS locks email field on register form to invite email
- [x] Amber notice on invite page showing required email
- [x] Accept invite flow (with auto-login support via ?next=)

### 8.3 Team Management Page (/team/)
- [x] Member list with role badges
- [x] Invite member (Admin/Owner only)
- [x] Remove member
- [x] Change member role
- [x] Seat usage display (x/y seats used)
- [x] Team page gated to Business plan

---

## 9. LEADS INBOX FEATURES *(not in original roadmap — fully built)*

- [x] Contact form on every public card page
- [x] CardLead model (name, email, phone, message, IP, is_read)
- [x] Leads Inbox page (/leads/) — lists all leads across user's cards
- [x] Unread badge counter in sidebar
- [x] Mark as read on open
- [x] Lead details display

---

## 10. BACKEND MODELS & DATA

### 10.1 Models implemented
- [x] User (Django default + auto-generated username from email)
- [x] Organization
- [x] OrganizationMember
- [x] BusinessCard
- [x] PhoneNumber
- [x] CountryCode (with flags and ISO codes)
- [x] CardView (analytics — IP, device, location, referrer)
- [x] ContactDownload (analytics)
- [x] CardInteraction (link click tracking)
- [x] CardLead
- [x] UserSettings (notifications + privacy preferences)
- [x] ActivityLog (login, password change, profile update, settings change)
- [ ] Subscriptions / Payments table *(Stripe — future)*

### 10.2 Auth & Security
- [x] Email-based registration (username auto-generated)
- [x] Email-based login (looks up username, authenticates)
- [x] Django sessions
- [x] CSRF protection (all forms)
- [x] Password hashing (Django PBKDF2)
- [x] Forgot / reset password (Django built-in views + custom templates)
- [x] update_session_auth_hash (stay logged in after password change)
- [x] Safe ?next= redirect (url_has_allowed_host_and_scheme)
- [x] @login_required on all authenticated views
- [ ] Social login (Google, LinkedIn) *(Advanced)*
- [ ] 2FA / TOTP *(Advanced)*
- [ ] Email verification on signup *(planned)*
- [ ] Rate limiting *(not yet)*

### 10.3 File Storage
- [x] Local media storage (MEDIA_ROOT / MEDIA_URL)
- [x] Profile photo, company logo, banner image upload
- [x] QR code generation (qrcode library, saved to media)
- [ ] Cloud storage (S3 / GCP) *(production requirement)*
- [ ] Image optimization / compression pipeline

### 10.4 Analytics Backend
- [x] IP geolocation (ip-api.com or similar) for CardView
- [x] User-agent parsing (device type detection)
- [x] Referrer classification (LinkedIn, Google, Direct, etc.)
- [x] Period comparison (current vs previous window)
- [x] CSV export view

---

## 11. PRIORITY IMPLEMENTATION ORDER (Updated)

### ✅ Phase 1 — Core Auth & Card MVP
1. ~~User registration & login~~ ✅
2. ~~Dashboard page~~ ✅
3. ~~Create / edit / delete card~~ ✅
4. ~~Public card view page~~ ✅

### ✅ Phase 2 — Enhanced Card Features
1. ~~Multiple phone numbers~~ ✅
2. ~~Image uploads (profile, logo, banner)~~ ✅
3. ~~Social media links~~ ✅
4. ~~Color customization~~ ✅
5. ~~QR code generation~~ ✅
6. ~~vCard download~~ ✅

### ✅ Phase 3 — Card Management
1. ~~My Cards page with filtering~~ ✅
2. ~~Search, filter, sort~~ ✅
3. ~~Bulk operations~~ ✅
4. ~~Archive / activate / deactivate~~ ✅
5. ~~Card duplication~~ ✅

### ✅ Phase 4 — Analytics & Tracking
1. ~~View & download tracking~~ ✅
2. ~~Analytics dashboard with charts~~ ✅
3. ~~Location, device, referrer tracking~~ ✅
4. ~~CSV export~~ ✅

### ✅ Phase 5 — Team Management *(added scope)*
1. ~~Organizations with plan tiers~~ ✅
2. ~~Member invites with email security~~ ✅
3. ~~Role-based permissions~~ ✅
4. ~~Leads capture & inbox~~ ✅

### ✅ Sprint A — Account Settings
1. ~~5-tab settings page~~ ✅
2. ~~Notification preferences (auto-save)~~ ✅
3. ~~Privacy settings (auto-save)~~ ✅
4. ~~Activity log timeline~~ ✅
5. ~~Delete account (typed confirmation)~~ ✅
6. ~~Password show/hide + strength bar~~ ✅

### 🔜 Sprint B — Card Polish
1. [ ] Card sharing modal (copy link, social share, WhatsApp)
2. [ ] Password show/hide on Login page
3. [ ] Terms & conditions checkbox on Register
4. [ ] Card type filter on My Cards
5. [ ] Stats mini-bar on My Cards page

### 🔜 Sprint C — Analytics Enhancement
1. [ ] Top Locations table (country/city, views, %)
2. [ ] Recent Activity table (on analytics page)
3. [ ] Average Time on Card metric
4. [ ] PDF export option

### 🔜 Sprint D — Landing Page Polish
1. [ ] Animated gradient hero section
2. [ ] Features section (6 cards with hover animations)
3. [ ] "How It Works" 3-step visual
4. [ ] Footer with all links
5. [ ] Final CTA banner section

### 🟡 Phase 6 — Real Billing
1. [ ] Real Stripe integration (webhooks, checkout)
2. [ ] Payment method management
3. [ ] Billing history + invoice generation
4. [ ] Subscription lifecycle (upgrade/downgrade/cancel)

### ❌ Advanced Features (Future)
1. [ ] 2FA (django-otp + TOTP)
2. [ ] Email verification on signup
3. [ ] Social login (Google, LinkedIn via django-allauth)
4. [ ] Real email notifications (SendGrid/Mailgun)
5. [ ] Email verification on signup
6. [ ] Custom domains
7. [ ] Multiple card templates / themes
8. [ ] Mobile app (React Native / Flutter)

---

## 12. TECHNICAL STATUS

### 12.1 Database (All migrated ✅)
- [x] Users, Organization, OrganizationMember
- [x] BusinessCard, PhoneNumber, CountryCode
- [x] CardView, ContactDownload, CardInteraction, CardLead
- [x] UserSettings, ActivityLog
- [ ] Subscriptions, Payments *(Stripe — future)*

### 12.2 File Storage
- [x] Local (MEDIA_ROOT) — profiles/, logos/, banners/, qr_codes/
- [ ] Cloud storage *(production: S3 or GCP)*

### 12.3 Security (Django defaults cover most)
- [x] CSRF on all forms
- [x] XSS prevention (Django auto-escaping)
- [x] SQL injection prevention (ORM)
- [x] Password hashing (PBKDF2)
- [x] Session security
- [x] Safe redirect validation
- [x] File upload type checking
- [ ] Rate limiting *(not yet)*
- [ ] HTTPS enforcement *(production config)*

### 12.4 Email Backend
- [x] Console backend (dev — prints to terminal)
- [ ] Production email service (SendGrid / Mailgun / SES)

### 12.5 External Libraries Used
- [x] Bootstrap 5.3 (UI)
- [x] Bootstrap Icons 1.11
- [x] Chart.js (analytics charts)
- [x] qrcode (Python — QR generation)
- [x] vobject (Python — vCard .vcf generation)
- [x] Pillow (image handling)
- [x] user-agents (device detection)
- [x] python-dateutil (date arithmetic)

---

## 13. MISSING / NOT YET BUILT

| Feature | Priority | Sprint |
|---|---|---|
| Password toggle on Login page | High | Sprint B |
| Card sharing modal (copy/social/WhatsApp) | High | Sprint B |
| Terms & conditions checkbox on register | Medium | Sprint B |
| Card type filter on My Cards | Medium | Sprint B |
| Stats bar on My Cards page | Low | Sprint B |
| Top Locations table (analytics) | Medium | Sprint C |
| Recent Activity table (analytics) | Medium | Sprint C |
| Average Time on Card | Low | Sprint C |
| Landing page polish (hero, features, footer) | Medium | Sprint D |
| Email verification on signup | Medium | Future |
| Help & Support / FAQ page | Low | Future |
| Real Stripe billing | High | Phase 6 |
| Invoice generation / download | Medium | Phase 6 |
| Activity log from card actions (create/edit/delete) | Low | Future |
| Avatar upload on profile | Low | Future |
| Bio / location fields on profile | Low | Future |
| 2FA authentication | Low | Advanced |
| Social login (Google, LinkedIn) | Medium | Advanced |
| Custom domains | Low | Advanced |
| Multiple card templates / themes | Medium | Advanced |
| Data export (GDPR) | Medium | Advanced |
| Mobile app | Low | Advanced |

---

**Document Version**: 2.0
**Last Updated**: February 27, 2026
**Status**: Active development — Sprint B next
**Project**: Virtual Business Card SaaS Platform (VCard Manager)
