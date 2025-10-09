#!/usr/bin/env python3
"""
Price Monitoring and Alerting System
Tracks price changes and sends notifications
"""
import json
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class PriceMonitor:
    def __init__(self):
        self.output_dir = Path(__file__).parent / "output"
        self.history_file = self.output_dir / "price_history.json"
        self.alerts_file = self.output_dir / "price_alerts.json"

    def load_history(self):
        """Load price history"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_history(self, history):
        """Save price history"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def load_latest_prices(self):
        """Load latest scraped prices"""
        latest_file = self.output_dir / "latest_products.json"
        if latest_file.exists():
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('products', [])
        return []

    def detect_changes(self):
        """Detect price changes"""
        history = self.load_history()
        current_products = self.load_latest_prices()

        changes = {
            'price_drops': [],
            'price_increases': [],
            'new_products': [],
            'timestamp': datetime.now().isoformat()
        }

        for product in current_products:
            product_key = f"{product['shop']}_{product['model']}"
            current_price = product.get('price_vnd')

            if not current_price:
                continue

            if product_key in history:
                old_price = history[product_key].get('price_vnd')
                if old_price and current_price != old_price:
                    change_pct = ((current_price - old_price) / old_price) * 100

                    change_info = {
                        'shop': product['shop'],
                        'model': product['model'],
                        'old_price': old_price,
                        'new_price': current_price,
                        'change_vnd': current_price - old_price,
                        'change_pct': round(change_pct, 2),
                        'url': product.get('url')
                    }

                    if current_price < old_price:
                        changes['price_drops'].append(change_info)
                    else:
                        changes['price_increases'].append(change_info)
            else:
                changes['new_products'].append({
                    'shop': product['shop'],
                    'model': product['model'],
                    'price': current_price,
                    'url': product.get('url')
                })

            # Update history
            history[product_key] = {
                'price_vnd': current_price,
                'last_updated': datetime.now().isoformat(),
                'model': product['model'],
                'shop': product['shop']
            }

        # Save updated history
        self.save_history(history)

        return changes

    def generate_alert_email(self, changes):
        """Generate email content for price changes"""
        if not changes['price_drops'] and not changes['new_products']:
            return None

        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                h2 { color: #2563eb; }
                .price-drop { background-color: #dcfce7; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .new-product { background-color: #e0f2fe; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .price { font-weight: bold; color: #16a34a; }
                .old-price { text-decoration: line-through; color: #6b7280; }
            </style>
        </head>
        <body>
            <h2>📊 MacBook Price Alert - {timestamp}</h2>
        """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M'))

        if changes['price_drops']:
            html += "<h3>💰 Price Drops</h3>"
            for drop in changes['price_drops']:
                html += f"""
                <div class="price-drop">
                    <strong>{drop['model']}</strong> at {drop['shop']}<br>
                    <span class="old-price">{drop['old_price']:,}₫</span> →
                    <span class="price">{drop['new_price']:,}₫</span><br>
                    <strong style="color: #16a34a;">Save {abs(drop['change_vnd']):,}₫ ({abs(drop['change_pct'])}%)</strong><br>
                    <a href="{drop['url']}">View Product</a>
                </div>
                """

        if changes['new_products']:
            html += "<h3>🆕 New Products</h3>"
            for product in changes['new_products'][:10]:  # Limit to 10
                html += f"""
                <div class="new-product">
                    <strong>{product['model']}</strong> at {product['shop']}<br>
                    Price: <span class="price">{product['price']:,}₫</span><br>
                    <a href="{product['url']}">View Product</a>
                </div>
                """

        html += """
        </body>
        </html>
        """

        return html

    def send_email_alert(self, changes, to_email, smtp_config=None):
        """Send email alert (requires SMTP configuration)"""
        if not smtp_config:
            print("⚠️  Email alerts not configured. Set SMTP settings to enable.")
            return False

        email_content = self.generate_alert_email(changes)
        if not email_content:
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"MacBook Price Alert - {len(changes['price_drops'])} Drops Found"
            msg['From'] = smtp_config['from_email']
            msg['To'] = to_email

            msg.attach(MIMEText(email_content, 'html'))

            with smtplib.SMTP(smtp_config['smtp_host'], smtp_config['smtp_port']) as server:
                server.starttls()
                server.login(smtp_config['smtp_user'], smtp_config['smtp_password'])
                server.send_message(msg)

            print(f"✅ Email alert sent to {to_email}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

    def run(self, send_email=False, email_to=None):
        """Run price monitoring"""
        print("🔍 Monitoring price changes...")

        changes = self.detect_changes()

        # Save alerts
        with open(self.alerts_file, 'w', encoding='utf-8') as f:
            json.dump(changes, f, indent=2, ensure_ascii=False)

        # Print summary
        print(f"\n{'='*60}")
        print("PRICE CHANGE SUMMARY")
        print(f"{'='*60}")
        print(f"📉 Price Drops: {len(changes['price_drops'])}")
        print(f"📈 Price Increases: {len(changes['price_increases'])}")
        print(f"🆕 New Products: {len(changes['new_products'])}")
        print(f"{'='*60}\n")

        if changes['price_drops']:
            print("💰 TOP PRICE DROPS:")
            for i, drop in enumerate(sorted(changes['price_drops'],
                                           key=lambda x: abs(x['change_vnd']),
                                           reverse=True)[:5], 1):
                print(f"{i}. {drop['model']} ({drop['shop']})")
                print(f"   {drop['old_price']:,}₫ → {drop['new_price']:,}₫")
                print(f"   Save {abs(drop['change_vnd']):,}₫ ({abs(drop['change_pct'])}%)")
                print()

        # Send email if configured
        if send_email and email_to:
            # Load SMTP config from environment or config file
            # For now, just save the alert
            print("💾 Alert saved to:", self.alerts_file)

        return changes


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Monitor MacBook price changes')
    parser.add_argument('--email', type=str, help='Send email alert to this address')

    args = parser.parse_args()

    monitor = PriceMonitor()
    monitor.run(send_email=bool(args.email), email_to=args.email)


if __name__ == '__main__':
    main()
