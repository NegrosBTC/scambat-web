import random
from datetime import datetime, timedelta

class ScamMessageGenerator:
    def __init__(self):
        # SMS scam templates (Hong Kong focused)
        self.sms_scam_templates = [
            {
                'text': "【Hang Seng Bank】URGENT: Your account has been suspended due to suspicious activity. Verify immediately: {link} or account will be closed. Ref: {ref_num}",
                'red_flags': ['urgent language', 'suspicious link', 'threat of account closure', 'fake reference number', 'account suspension threat']
            },
            {
                'text': "🎉Congratulations! You've won HK${amount} in Mark Six lottery! Claim now: {link} Processing fee: HK$500. Reply STOP to opt out.",
                'red_flags': ['fake lottery win', 'upfront fee request', 'suspicious link', 'too good to be true', 'Mark Six impersonation']
            },
            {
                'text': "【SF Express】Your package delivery failed. Pay HK$39 handling fee: {link} Package will be returned to sender if not paid within 24hrs.",
                'red_flags': ['fake delivery notice', 'payment request', 'urgent deadline', 'suspicious link', 'courier impersonation']
            },
            {
                'text': "【HSBC Security】Suspicious login from Mainland China detected. Verify identity: {link} If this wasn't you, click immediately to secure account.",
                'red_flags': ['fake security alert', 'phishing link', 'urgency tactics', 'fear-based messaging', 'bank impersonation']
            },
            {
                'text': "【IRD Notice】You owe HK${amount} in unpaid taxes. Avoid legal action by paying immediately: {link} Case #{ref_num}",
                'red_flags': ['government impersonation', 'tax scam', 'legal threats', 'immediate payment demand', 'IRD impersonation']
            },
            {
                'text': "【Octopus Alert】Your Octopus card will expire soon. Renew now to avoid service interruption: {link} Renewal fee: HK$50",
                'red_flags': ['Octopus impersonation', 'false expiry notice', 'renewal fee scam', 'suspicious link', 'service interruption threat']
            },
            {
                'text': "【SmartOne】FINAL NOTICE: Your mobile plan will auto-renew for HK${amount}. Cancel here: {link} or call {phone}",
                'red_flags': ['fake subscription', 'auto-renewal scam', 'pressure tactics', 'suspicious contact info', 'telecom impersonation']
            },
            {
                'text': "【AlipayHK】Your account shows unusual spending of HK${amount}. Secure your account: {link} Contact support: {phone}",
                'red_flags': ['payment app impersonation', 'fake security alert', 'suspicious spending claim', 'phishing link', 'fake support number']
            },
            {
                'text': "【BOC Hong Kong】Your credit card ending in {card_digits} has been charged HK${amount}. Dispute immediately: {link}",
                'red_flags': ['bank impersonation', 'fake charge notification', 'partial card number trick', 'dispute scam', 'phishing link']
            }
        ]
        
        # SMS legitimate templates (Hong Kong focused)
        self.sms_legitimate_templates = [
            {
                'text': "【Hong Kong Hospital】Your appointment with Dr. Chan on {date} at 2:00 PM has been confirmed. Queen Mary Hospital. Reply STOP to opt out.",
                'sender_type': 'medical'
            },
            {
                'text': "【PARKnSHOP】Your order #{order_num} is ready for pickup at Causeway Bay store. Collection hours: 9AM-10PM. Thank you!",
                'sender_type': 'retail'
            },
            {
                'text': "【Hong Kong Public Library】Reminder: Your borrowed books are due tomorrow. Renew online at hkpl.gov.hk or return to avoid late fees.",
                'sender_type': 'library'
            },
            {
                'text': "【Cathay Pacific】Your flight CX{flight_num} to {destination} is on time. Check-in opens 3 hours before departure at HKIA.",
                'sender_type': 'airline'
            },
            {
                'text': "【Watsons】Your prescription for {medication} is ready for pickup at Nathan Road branch. Opening hours: 8AM-11PM daily.",
                'sender_type': 'pharmacy'
            },
            {
                'text': "【MTR】Service update: Tsuen Wan Line experiencing 5-min delays due to signal fault. Normal service resuming shortly. Sorry for inconvenience.",
                'sender_type': 'transport'
            },
            {
                'text': "【OpenRice】Thanks for dining at {restaurant}! Rate your experience and earn points. Your receipt: HK${amount} on {date}",
                'sender_type': 'dining'
            }
        ]
        
        # Email scam templates (Hong Kong focused)
        self.email_scam_templates = [
            {
                'subject': 'Urgent: HSBC Account Verification Required',
                'sender_name': 'HSBC Security Team',
                'sender_domain': 'hsbc-security.net',
                'text': "Dear Valued Customer,\n\nWe have detected unusual activity on your HSBC account from an IP address in Mainland China. To protect your funds, we need you to verify your account information immediately.\n\nClick here to verify: {link}\n\nFailure to verify within 24 hours will result in account suspension and potential fund freezing.\n\nThank you,\nHSBC Security Department\nHong Kong",
                'red_flags': ['fake bank email', 'phishing link', 'account suspension threat', 'suspicious domain', 'urgent verification request', 'mainland China reference']
            },
            {
                'subject': 'Inheritance Claim: HK$8.5 Million from Late Mr. Wong',
                'sender_name': 'Solicitor James Liu',
                'sender_domain': 'hk-legal-services.biz',
                'text': "Dear Friend,\n\nI am contacting you regarding an inheritance of HK$8.5 Million left by my late client Mr. Wong Tai Sin who shares your surname. As his legal representative in Hong Kong, I need your assistance to transfer these funds.\n\nPlease reply with your HKID and banking details to proceed with the inheritance claim.\n\nBest regards,\nSolicitor James Liu\nCentral Legal Chambers\nHong Kong",
                'red_flags': ['inheritance scam', 'advance fee fraud', 'too good to be true', 'requests HKID', 'impersonation', 'fake legal chambers']
            },
            {
                'subject': 'AlipayHK Payment Confirmation - HK$2,999',
                'sender_name': 'AlipayHK Service',
                'sender_domain': 'alipayhk-security.com',
                'text': "Hello,\n\nYour AlipayHK account has been charged HK$2,999 for iPhone 15 Pro purchase from unauthorized merchant.\n\nTransaction ID: {ref_num}\nMerchant: Sham Shui Po Electronics\n\nIf you did not authorize this payment, please contact us immediately at: {phone}\n\nDispute this transaction: {link}\n\nThank you,\nAlipayHK Security Team",
                'red_flags': ['fake payment notification', 'impersonation of AlipayHK', 'suspicious domain', 'fake phone number', 'phishing link', 'unauthorized merchant claim']
            },
            {
                'subject': 'Action Required: Update Your Apple ID Information',
                'sender_name': 'Apple Hong Kong',
                'sender_domain': 'apple-hk-update.org',
                'text': "Dear User,\n\nYour Apple ID will be suspended due to unusual sign-in activity from {location}.\n\nTo prevent suspension and protect your Hong Kong App Store purchases, please update your security information:\n{link}\n\nThis action is required within 48 hours.\n\nApple Hong Kong Security Team",
                'red_flags': ['fake Apple email', 'account suspension threat', 'suspicious domain', 'phishing link', 'impersonation', 'App Store reference']
            },
            {
                'subject': 'Congratulations! HK$5,000 Wellcome Gift Voucher Winner',
                'sender_name': 'Wellcome Rewards',
                'sender_domain': 'wellcome-rewards.net',
                'text': "Congratulations!\n\nYou have been selected to receive a HK$5,000 Wellcome supermarket gift voucher in our anniversary promotion!\n\nTo claim your prize, please complete our customer survey:\n{link}\n\nThis offer expires in 24 hours. Valid at all Wellcome stores in Hong Kong.\n\nWellcome Customer Service",
                'red_flags': ['fake prize notification', 'impersonation of Wellcome', 'suspicious domain', 'survey scam', 'urgency tactics', 'supermarket voucher scam']
            },
            {
                'subject': 'MPF Account Statement - Urgent Action Required',
                'sender_name': 'MPF Authority',
                'sender_domain': 'mpf-authority.org',
                'text': "Dear MPF Member,\n\nYour Mandatory Provident Fund account requires immediate verification due to new HKMA regulations.\n\nFunds totaling HK${amount} are pending release. Complete verification here: {link}\n\nContact MPF Hotline: {phone}\n\nMPF Schemes Authority\nHong Kong",
                'red_flags': ['MPF impersonation', 'fake government authority', 'urgent verification', 'funds pending scam', 'suspicious domain', 'fake regulations']
            }
        ]
        
        # Email legitimate templates (Hong Kong focused)
        self.email_legitimate_templates = [
            {
                'subject': 'Your PARKnSHOP Online Order Confirmation #OR{order_num}',
                'sender_name': 'PARKnSHOP Online',
                'sender_domain': 'parknshop.com',
                'text': "Hello {customer_name},\n\nThank you for your order! Your PARKnSHOP online order #OR{order_num} has been confirmed.\n\nOrder Details:\n- {item_name}\n- Quantity: 1\n- Total: HK${amount}\n\nDelivery Address: {district}, Hong Kong\nExpected delivery: {date}\n\nTrack your order at parknshop.com/myaccount\n\nThank you for shopping with PARKnSHOP!",
                'sender_type': 'retail'
            },
            {
                'subject': 'Password Reset Request - HKID Portal',
                'sender_name': 'HKID Portal Support',
                'sender_domain': 'gov.hk',
                'text': "Hi there,\n\nYou recently requested to reset your password for your HKID Portal account.\n\nTo reset your password, click the link below:\n{reset_link}\n\nIf you didn't request this, please ignore this email.\n\nThanks,\nHKID Portal Team\nHong Kong Government",
                'sender_type': 'government'
            },
            {
                'subject': 'Welcome to Now TV!',
                'sender_name': 'Now TV Hong Kong',
                'sender_domain': 'nowtv.com',
                'text': "Welcome to Now TV!\n\nYour subscription is now active. You can start watching immediately on all your devices.\n\nPlan: {plan_name}\nMonthly fee: HK${amount}\nNext billing date: {date}\n\nStart watching at nowtv.com or use the Now Player app.\n\nThe Now TV Team\nHong Kong",
                'sender_type': 'entertainment'
            },
            {
                'subject': 'Your Receipt from Starbucks Hong Kong',
                'sender_name': 'Starbucks Hong Kong',
                'sender_domain': 'starbucks.com.hk',
                'text': "Thank you for visiting Starbucks!\n\nStore: {store_location}\nDate: {date}\nTime: {time}\n\nOrder Summary:\n- {item_name}: HK${item_price}\n- Service Charge: HK${service_charge}\nTotal: HK${total}\n\nEarn Stars with every purchase using the Starbucks Hong Kong app!\n\nStarbucks Hong Kong",
                'sender_type': 'receipt'
            },
            {
                'subject': 'Cathay Pacific Booking Confirmation',
                'sender_name': 'Cathay Pacific',
                'sender_domain': 'cathaypacific.com',
                'text': "Dear {customer_name},\n\nYour booking has been confirmed!\n\nFlight: CX{flight_num}\nRoute: Hong Kong (HKG) → {destination}\nDate: {date}\nBooking Reference: {booking_ref}\n\nCheck-in opens 48 hours before departure at cathaypacific.com\n\nThank you for choosing Cathay Pacific.\n\nCathay Pacific Airways\nHong Kong",
                'sender_type': 'airline'
            }
        ]
        
        # Hong Kong phone numbers
        self.scam_phone_numbers = [
            '+852 6123 4567', '+852 9876 5432', '+852 5555 1234', '+852 9999 8888',
            '+852 6666 7777', '+852 8888 9999', '+852 5432 1098', '+852 7777 6666'
        ]
        
        self.legitimate_phone_numbers = [
            '+852 2123 4567', '+852 3123 4567', '+852 2987 6543', '+852 3456 7890',
            '+852 2888 8888', '+852 3999 9999', '+852 2345 6789', '+852 3777 7777'
        ]
        
        # Suspicious domains (Hong Kong themed but fake)
        self.suspicious_domains = [
            'hsbc-security.net', 'alipayhk-security.com', 'wellcome-rewards.net',
            'apple-hk-update.org', 'hk-legal-services.biz', 'mpf-authority.org',
            'octopus-renewal.com', 'smartone-billing.net', 'cathay-booking.org'
        ]
        
        # Legitimate Hong Kong domains
        self.legitimate_domains = [
            'parknshop.com', 'gov.hk', 'nowtv.com', 'starbucks.com.hk',
            'cathaypacific.com', 'hsbc.com.hk', 'hangseng.com', 'octopus.com.hk'
        ]
        
        # Hong Kong locations/districts
        self.hk_districts = [
            'Central', 'Admiralty', 'Wan Chai', 'Causeway Bay', 'Tsim Sha Tsui',
            'Mong Kok', 'Yau Ma Tei', 'Sha Tin', 'Tai Po', 'Tuen Mun',
            'Kwun Tong', 'Wong Tai Sin', 'Sham Shui Po', 'Tin Hau', 'North Point'
        ]
        
        # Hong Kong restaurants for OpenRice
        self.hk_restaurants = [
            'Dim Sum Square', 'Maxims Palace', 'Crystal Jade', 'Tim Ho Wan',
            'Kam Wah Cafe', 'Tsui Wah Restaurant', 'Yung Kee Restaurant', 'Mott 32'
        ]
        
        # Hong Kong specific items
        self.hk_items = [
            'Instant Noodles (Nissin)', 'Vita Lemon Tea', 'Hong Kong Style Milk Tea',
            'Pineapple Bun', 'Egg Tart', 'Red Bean Ice Cream', 'Pocky Sticks'
        ]

    def generate_message(self, is_scam, message_type='sms'):
        """Generate a message based on type (sms or email)"""
        if message_type == 'email':
            return self.generate_email_message(is_scam)
        else:
            return self.generate_sms_message(is_scam)
    
    def generate_sms_message(self, is_scam):
        """Generate an SMS message"""
        if is_scam:
            template = random.choice(self.sms_scam_templates)
            phone_number = random.choice(self.scam_phone_numbers)
            
            # Fill in template variables
            text = template['text'].format(
                link=self._generate_suspicious_link(),
                amount=random.choice([299, 499, 999, 1999, 2999, 4999, 8888, 9999]),
                ref_num=self._generate_reference_number(),
                phone=random.choice(self.scam_phone_numbers),
                card_digits=random.randint(1000, 9999)
            )
            
            return {
                'type': 'sms',
                'phone_number': phone_number,
                'text': text,
                'is_scam': True,
                'red_flags': template['red_flags']
            }
        else:
            template = random.choice(self.sms_legitimate_templates)
            phone_number = random.choice(self.legitimate_phone_numbers)
            
            # Fill in template variables
            text = template['text'].format(
                date=self._generate_future_date(),
                order_num=self._generate_order_number(),
                flight_num=random.randint(100, 999),
                destination=random.choice(['Tokyo', 'Seoul', 'Bangkok', 'Singapore', 'London', 'Sydney']),
                medication=random.choice(['Panadol', 'Vitamin C', 'Cold Medicine', 'Eye Drops']),
                restaurant=random.choice(self.hk_restaurants),
                amount=random.choice([45, 68, 89, 120, 156, 200, 288])
            )
            
            return {
                'type': 'sms',
                'phone_number': phone_number,
                'text': text,
                'is_scam': False,
                'red_flags': []
            }
    
    def generate_email_message(self, is_scam):
        """Generate an email message"""
        if is_scam:
            template = random.choice(self.email_scam_templates)
            sender_email = f"{template['sender_name'].lower().replace(' ', '.')}@{template['sender_domain']}"
            
            # Fill in template variables
            text = template['text'].format(
                link=self._generate_suspicious_link(),
                amount=random.choice([1999, 2999, 4999, 8888, 12888, 18888]),
                ref_num=self._generate_reference_number(),
                phone=random.choice(self.scam_phone_numbers),
                location=random.choice(['Mainland China', 'Macau', 'Taiwan', 'Unknown Location', 'Overseas'])
            )
            
            return {
                'type': 'email',
                'sender_email': sender_email,
                'sender_name': template['sender_name'],
                'subject': template['subject'],
                'text': text,
                'is_scam': True,
                'red_flags': template['red_flags']
            }
        else:
            template = random.choice(self.email_legitimate_templates)
            sender_email = f"noreply@{template['sender_domain']}"
            
            # Fill in template variables
            text = template['text'].format(
                customer_name=random.choice(['John Chan', 'Mary Wong', 'David Lee', 'Sarah Lam', 'Michael Ng']),
                order_num=self._generate_order_number(),
                item_name=random.choice(self.hk_items),
                amount=random.choice([89, 128, 168, 298, 388, 488]),
                date=self._generate_future_date(),
                plan_name=random.choice(['Basic', 'Premium', 'Sports Pack', 'Movie Pack']),
                store_location=f"{random.choice(self.hk_districts)} Branch",
                time=f"{random.randint(7, 22)}:{random.randint(0, 59):02d}",
                item_price=random.choice([38, 42, 48, 52, 58]),
                service_charge=round(random.choice([3.8, 4.2, 4.8, 5.2]), 1),
                total=round(random.choice([41.8, 46.2, 52.8, 57.2]), 1),
                reset_link='https://www.gov.hk/hkid/reset/abc123def456',
                flight_num=random.randint(100, 999),
                destination=random.choice(['NRT', 'ICN', 'BKK', 'SIN', 'LHR', 'SYD']),
                booking_ref=self._generate_booking_reference(),
                district=random.choice(self.hk_districts)
            )
            
            return {
                'type': 'email',
                'sender_email': sender_email,
                'sender_name': template['sender_name'],
                'subject': template['subject'],
                'text': text,
                'is_scam': False,
                'red_flags': []
            }
    
    def _generate_suspicious_link(self):
        """Generate a suspicious-looking link"""
        domains = [
            'bit.ly/hk3x7k9m', 'tinyurl.com/hkverify99', 'short.link/hkbank123',
            't.co/hkscam456', 'ow.ly/hkpay789', 'goo.gl/hkwarn321'
        ]
        return f"https://{random.choice(domains)}"
    
    def _generate_reference_number(self):
        """Generate a fake reference number (Hong Kong style)"""
        prefixes = ['HK', 'REF', 'TXN', 'CASE', 'ID']
        return f"{random.choice(prefixes)}{random.randint(100000, 999999)}"
    
    def _generate_order_number(self):
        """Generate a realistic order number"""
        return f"HK{random.randint(100000, 999999)}"
    
    def _generate_booking_reference(self):
        """Generate airline booking reference"""
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return ''.join(random.choices(letters, k=6))
    
    def _generate_future_date(self):
        """Generate a future date"""
        future_date = datetime.now() + timedelta(days=random.randint(1, 30))
        return future_date.strftime("%d %B %Y")