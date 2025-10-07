# VietMac Analytics Guide

This guide shows you how to track and analyze user behavior on VietMac using PostHog.

## 📊 Key Metrics Being Tracked

### 1. **MacBook Model Preferences**
Track which MacBook models users are most interested in.

**Events:**
- `filter_model_selected` - When users filter by model
- `macbook_listing_clicked` - When users click on a listing

**Properties:**
- `model` - Full model name (e.g., "MacBook Pro 14-inch M4")
- `model_type` - Type (MacBook Air or MacBook Pro)
- `screen_size` - Screen size (13", 14", 15", 16")
- `chipset` - Chip type (M2, M3, M4, M4 Pro, M4 Max, M3 Max)

### 2. **Screen Size Preferences**
See which screen sizes are most popular.

**Event:** `filter_screen_size_selected`

**Properties:**
- `screen_size` - Selected screen size
- `model` - Current model filter
- `chipset` - Current chipset filter

### 3. **Currency Preferences**
Track which currencies users prefer.

**Event:** `currency_changed`

**Properties:**
- `from` - Previous currency
- `to` - New currency

### 4. **User Interactions**
Monitor how users engage with the site.

**Events:**
- `macbook_listing_clicked` - User clicks on a MacBook listing
- `prices_refreshed` - User refreshes prices
- `bargain_toggle_clicked` - User enables/disables bargaining

**Rich Data Captured on Listing Clicks:**
- Shop name
- Full configuration details
- Prices (VND, converted, final)
- VAT refund amount
- Bargain discount applied
- Device type (mobile/desktop)

## 🎯 How to View These Metrics in PostHog

### Option 1: Quick Insights

1. Go to https://app.posthog.com
2. Navigate to **"Activity"** in the left sidebar
3. You'll see all events in real-time
4. Click on any event to see its properties

### Option 2: Create Custom Insights

#### **Most Popular MacBook Models**

1. Go to **"Product Analytics" → "Insights"**
2. Click **"New insight"**
3. Select **"Trends"**
4. Configure:
   - Event: `macbook_listing_clicked`
   - Break down by: `model_type`
   - Date range: Last 30 days
5. Click **"Save"**

**What you'll see:** Bar chart showing MacBook Air vs MacBook Pro clicks

#### **Screen Size Distribution**

1. Create new **Trends** insight
2. Configure:
   - Event: `filter_screen_size_selected` OR `macbook_listing_clicked`
   - Break down by: `screen_size`
   - Date range: Last 30 days
3. Click **"Save"**

**What you'll see:** Which screen sizes (13", 14", 15", 16") are most viewed

#### **Popular Chipsets**

1. Create new **Trends** insight
2. Configure:
   - Event: `macbook_listing_clicked`
   - Break down by: `chipset`
   - Date range: Last 30 days
3. Click **"Save"**

**What you'll see:** M2 vs M3 vs M4 popularity

#### **Currency Preferences**

1. Create new **Trends** insight
2. Configure:
   - Event: `currency_changed`
   - Break down by: `to`
   - Date range: Last 30 days
3. Click **"Save"**

**What you'll see:** Which currencies users prefer (INR, USD, EUR)

#### **Shop Click-Through Rate**

1. Create new **Trends** insight
2. Configure:
   - Event: `macbook_listing_clicked`
   - Break down by: `shop`
   - Date range: Last 30 days
3. Click **"Save"**

**What you'll see:** CellphoneS vs ShopDunk vs FPT Shop clicks

#### **Mobile vs Desktop Usage**

1. Create new **Trends** insight
2. Configure:
   - Event: `macbook_listing_clicked`
   - Break down by: `device`
   - Date range: Last 30 days
3. Click **"Save"**

**What you'll see:** Mobile vs Desktop engagement

### Option 3: Create a Dashboard

Combine all insights into one dashboard:

1. Go to **"Dashboards"** → **"New dashboard"**
2. Name it: "VietMac User Preferences"
3. Click **"Add insight"**
4. Add all the insights you created above
5. Arrange them in a grid layout

**Recommended Dashboard Layout:**
```
┌─────────────────────────┬─────────────────────────┐
│ MacBook Model Types     │ Screen Size Distribution│
├─────────────────────────┼─────────────────────────┤
│ Popular Chipsets        │ Currency Preferences    │
├─────────────────────────┼─────────────────────────┤
│ Shop Performance        │ Mobile vs Desktop       │
├─────────────────────────┴─────────────────────────┤
│ Listing Clicks Over Time (Full Width)            │
└───────────────────────────────────────────────────┘
```

## 📈 Advanced Analytics

### Conversion Funnel

Track how many users go from viewing → filtering → clicking:

1. Go to **"Product Analytics" → "Funnels"**
2. Click **"New funnel"**
3. Add steps:
   - Step 1: `$pageview`
   - Step 2: Any filter event (`filter_model_selected`, `filter_screen_size_selected`, or `filter_chipset_selected`)
   - Step 3: `macbook_listing_clicked`
4. Click **"Save"**

**What you'll see:** Conversion rate from visit → filter → click

### Retention Analysis

See if users come back:

1. Go to **"Product Analytics" → "Retention"**
2. Configure:
   - Cohort: Users who triggered `$pageview`
   - Return event: `$pageview`
   - Period: Weekly
3. Click **"Save"**

**What you'll see:** Week-over-week retention rates

### Session Recordings

Watch actual user sessions:

1. Go to **"Session Replay"** in the left sidebar
2. Filter by:
   - Events: `macbook_listing_clicked`
   - Date: Last 7 days
3. Click on any recording to watch

**What you'll see:** Video playback of user interactions

## 🔍 Filtering Tips

You can filter any insight by properties:

- **By Currency:** Add filter `currency = INR`
- **By Model Type:** Add filter `model_type = MacBook Pro`
- **By Screen Size:** Add filter `screen_size = 14"`
- **By Shop:** Add filter `shop = CellphoneS`
- **By Bargain Users:** Add filter `bargain_discount > 0`

## 📊 Example Questions You Can Answer

1. **What's the most popular MacBook?**
   - Insight: Trends → `macbook_listing_clicked` → Break down by `model`

2. **Do users prefer Pro or Air?**
   - Insight: Trends → `macbook_listing_clicked` → Break down by `model_type`

3. **Which screen size sells best?**
   - Insight: Trends → `macbook_listing_clicked` → Break down by `screen_size`

4. **Are M4 chips more popular than M3?**
   - Insight: Trends → `macbook_listing_clicked` → Break down by `chipset`

5. **Which currency do most users use?**
   - Insight: Trends → `currency_changed` → Break down by `to`

6. **Which shop gets the most clicks?**
   - Insight: Trends → `macbook_listing_clicked` → Break down by `shop`

7. **Do mobile or desktop users click more?**
   - Insight: Trends → `macbook_listing_clicked` → Break down by `device`

8. **What's the average bargain discount?**
   - Insight: Trends → `macbook_listing_clicked` → Formula mode → Average of `bargain_discount`

9. **What's the conversion rate from view to click?**
   - Funnel: `$pageview` → `macbook_listing_clicked`

10. **What price range gets the most clicks?**
    - Insight: Trends → `macbook_listing_clicked` → Break down by `final_price` (bucketed)

## 🚀 Quick Start Checklist

- [ ] Visit https://app.posthog.com
- [ ] Go to "Activity" to see events in real-time
- [ ] Create insight: "Most Popular Models"
- [ ] Create insight: "Screen Size Preferences"
- [ ] Create insight: "Currency Distribution"
- [ ] Create insight: "Shop Performance"
- [ ] Combine all insights into a dashboard
- [ ] Watch some session recordings
- [ ] Set up weekly email reports (Settings → Subscriptions)

## 💡 Pro Tips

1. **Set up email reports:** Get weekly analytics delivered to your inbox
   - Dashboard → ⋯ → "Subscribe" → Set frequency

2. **Export data:** Download CSV for external analysis
   - Any insight → ⋯ → "Export"

3. **Share insights:** Get shareable links
   - Any insight → "Share" → Copy link

4. **Create alerts:** Get notified of anomalies
   - Any insight → ⋯ → "Create alert"

5. **Compare periods:** See week-over-week changes
   - Any insight → "Compare to" → Previous period

## 📞 Need Help?

- PostHog Docs: https://posthog.com/docs
- VietMac PostHog: https://app.posthog.com
- Setup Guide: See `POSTHOG_SETUP.md`
