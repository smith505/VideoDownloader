# PropellerAds Setup Guide

This guide will help you set up PropellerAds to monetize your video downloader with optional ad viewing.

## Step 1: Sign Up for PropellerAds

1. Go to **https://publishers.propellerads.com/**
2. Click **"Sign Up"** or **"Join Now"**
3. Fill in your details:
   - Email address
   - Password
   - Website URL (use your Render deployment URL)
   - Select "Publisher" account type
4. Verify your email address
5. Complete your profile in the dashboard

## Step 2: Add Your Website

1. Log in to PropellerAds dashboard
2. Go to **"Websites"** → **"Add Website"**
3. Enter your website URL (your Render URL)
4. Select website category: **"Entertainment" or "Downloads"**
5. Click **"Add Website"**

**Note:** PropellerAds usually approves sites within 24 hours!

## Step 3: Create an Ad Zone

Once your site is approved:

1. Go to **"Ad Zones"** → **"Create Ad Zone"**
2. Select your website from the dropdown
3. Choose ad format: **"Onclick (Popunder)"** or **"Interstitial"**
   - **Recommended:** Onclick for better user experience
4. Configure settings (use defaults)
5. Click **"Create"**
6. You'll receive a **Zone ID** (looks like: `1234567`)

## Step 4: Add Zone ID to Your Code

1. Open `index.html`
2. Find this line (around line 13):
   ```javascript
   var propellerAdsZoneId = 'XXXXXX';
   ```
3. Replace `XXXXXX` with your actual Zone ID:
   ```javascript
   var propellerAdsZoneId = '1234567';
   ```
4. Save and commit the changes
5. Push to GitHub (will auto-deploy on Render)

## Step 5: Test Your Ads

1. Visit your deployed site
2. Click **"📺 Watch Ad to Support"** button
3. The ad should now display!
4. Monitor performance in PropellerAds dashboard

## Alternative Ad Format (Interstitial Video)

If you want video ads instead of popunders:

1. In PropellerAds dashboard, create a new zone
2. Select **"Interstitial Video"** format
3. Get the Zone ID
4. Update `index.html` with the new Zone ID

## Expected Earnings

- **CPM:** $1-5 per 1000 ad views (varies by country)
- **Revenue split:** You keep 80%, PropellerAds takes 20%
- **Payment:** Net-30 (paid monthly)
- **Minimum payout:** $5 (PayPal, Payoneer, Wire)

## Payment Setup

1. Go to **"Billing"** in dashboard
2. Add your payment method:
   - PayPal (easiest)
   - Payoneer
   - Wire Transfer
   - Bitcoin
3. Set payment threshold (minimum $5)

## Tips for Better Performance

- PropellerAds works best with consistent traffic
- Encourage users to disable ad blockers (for the "Watch Ad" feature)
- Monitor your stats regularly in the dashboard
- Try different ad formats to see what works best
- Combine with Ko-fi donations for dual revenue streams

## Troubleshooting

### Ads not showing?
- Check that Zone ID is correct in `index.html`
- Make sure your site is approved
- Disable ad blockers for testing
- Check browser console for errors

### Low earnings?
- PropellerAds CPM varies by visitor location
- US/UK traffic pays more than other regions
- Video ads typically pay better than popunders
- Consider upgrading to premium ad formats

## Support

- PropellerAds Support: support@propellerads.com
- Dashboard: https://publishers.propellerads.com/
- Documentation: https://propellerads.com/blog/

---

**Need help?** Contact PropellerAds support or check their extensive documentation and tutorials.
