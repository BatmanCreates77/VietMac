# PostHog Analytics Setup Guide

This project uses PostHog for analytics and product insights.

## 🚀 Quick Setup (5 minutes)

### Step 1: Sign up for PostHog

1. Go to https://app.posthog.com/signup
2. Create a free account (1M events/month free)
3. Create a new project

### Step 2: Get Your API Key

1. After creating your project, you'll see your **Project API Key**
2. Copy this key (it looks like: `phc_xxxxxxxxxxxxxxxxxxxxxxxxxx`)

### Step 3: Add Environment Variables

1. Create a `.env.local` file in the root directory:
```bash
cp .env.local.example .env.local
```

2. Add your PostHog credentials:
```env
NEXT_PUBLIC_POSTHOG_KEY=phc_your_actual_key_here
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
```

### Step 4: Restart Your Server

```bash
pm2 restart vietmac
# or
npm run dev
```

That's it! Analytics are now tracking.

---

## 📊 Events Being Tracked

### Page Views
- Automatic tracking of all page visits
- Tracks referrer, device, browser, country

### User Interactions

**Currency Changes**
```javascript
Event: 'currency_changed'
Properties: { from: 'INR', to: 'USD' }
```

**Refresh Prices**
```javascript
Event: 'refresh_prices_clicked'
Properties: { currency: 'INR' }
```

**MacBook Listing Clicked**
```javascript
Event: 'macbook_listing_clicked'
Properties: {
  shop: 'FPT Shop',
  model: 'MacBook Pro 14" M4',
  category: 'M4',
  price_vnd: 38090000,
  final_price: 128222,
  currency: 'INR'
}
```

**Bargain Slider Toggle**
```javascript
Event: 'bargain_toggle_clicked'
Properties: { enabled: true }
```

---

## 🎯 What You Can Do with PostHog

### 1. **Dashboard** (Free)
- Real-time visitor count
- Top pages
- Conversion funnels
- User retention

### 2. **Session Recordings** (Free tier: 5K recordings/month)
- Watch users navigate your site
- See exactly where they click
- Identify UX issues

### 3. **Insights** (Free)
- Which MacBook models get the most clicks?
- Which retailers convert best?
- What's the average time before users click to store?
- Currency preference breakdown

### 4. **Funnels** (Free)
Track conversion flow:
```
Page Visit → Currency Select → View Prices → Click Listing → External Link
```

### 5. **Feature Flags** (Free)
- A/B test different features
- Roll out features to specific users
- Kill switches for bugs

---

## 📈 Key Metrics to Monitor

### Traffic Metrics
- **Daily Active Users (DAU)**
- **Unique visitors**
- **Bounce rate**
- **Time on site**

### Engagement Metrics
- **Most clicked MacBook models**
- **Popular retailers** (FPT Shop vs ShopDunk vs CellphoneS)
- **Currency distribution** (INR vs USD vs EUR)
- **Filter usage** (Model, Chipset, Screen Size)
- **Bargain slider adoption**

### Conversion Metrics
- **Click-through rate to stores**
- **Time to first click**
- **Most profitable price ranges**

---

## 🔧 Advanced Setup

### Enable Session Recordings

1. In PostHog dashboard, go to **Settings → Project → Recordings**
2. Toggle "Record user sessions" ON
3. Set filters if needed (e.g., only record users who clicked a listing)

### Create Your First Funnel

1. Go to **Insights → New Insight → Funnel**
2. Add steps:
   - Step 1: Pageview
   - Step 2: currency_changed
   - Step 3: macbook_listing_clicked
3. See conversion rates between each step

### Set Up Alerts

1. Go to **Insights → Create Alert**
2. Example: "Alert me when DAU drops below 100"
3. Get Slack/email notifications

---

## 🔒 Privacy & GDPR

PostHog is GDPR-compliant:
- No cookies required (uses localStorage)
- EU data hosting available
- Auto-capture can be disabled
- User data can be deleted

### Disable Auto-Capture (if needed)

```javascript
// In app/providers/posthog-provider.js
posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY, {
  autocapture: false, // Disable automatic event capture
  capture_pageview: true, // Keep pageview tracking
})
```

---

## 📱 Testing in Development

PostHog debug mode is automatically enabled in development:

```javascript
// Check browser console for PostHog events
// You'll see: [PostHog] Event captured: currency_changed
```

---

## 🎓 Resources

- [PostHog Docs](https://posthog.com/docs)
- [Next.js Integration](https://posthog.com/docs/libraries/next-js)
- [Event Naming Best Practices](https://posthog.com/docs/data/events)
- [Dashboard Templates](https://posthog.com/templates)

---

## 💡 Pro Tips

1. **Create Custom Dashboards**
   - Make a "MacBook Performance" dashboard
   - Track which models drive the most traffic

2. **Set Up Weekly Reports**
   - Email yourself key metrics every Monday
   - Track growth over time

3. **Use Cohorts**
   - Group users by currency preference
   - See behavior differences between INR vs USD users

4. **Monitor Performance**
   - PostHog has minimal impact (~2KB)
   - Events are batched and sent async

---

## 🐛 Troubleshooting

### Events not showing up?

1. Check `.env.local` file exists
2. Verify API key is correct
3. Check browser console for errors
4. Make sure PostHog is initialized (check Network tab)

### Need to test without affecting production data?

Create a separate PostHog project for development:

```env
# .env.local
NEXT_PUBLIC_POSTHOG_KEY=phc_dev_key_here  # Different key for dev
```

---

## 📊 Sample Dashboard Setup

Here's a recommended dashboard layout:

### Overview Panel
- Total visitors (last 7 days)
- Unique visitors
- Average session duration
- Bounce rate

### Engagement Panel
- Top 5 MacBook models clicked
- Currency distribution (pie chart)
- Bargain slider usage (%)
- Filter usage breakdown

### Conversion Panel
- Click-through rate to stores
- Funnel: View → Filter → Click
- Time to first listing click
- Top performing retailers

---

Need help? Check PostHog community: https://posthog.com/questions
