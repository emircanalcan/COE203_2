# tests.py
import unittest
from datetime import datetime
from core import TokenData, TokenCategory, CryptoAnalyzer

class TestCryptoSystem(unittest.TestCase):
    
    def setUp(self):
        # Test verisi oluştur
        self.sample_tokens = [
            TokenData(
                id="BTCUSDT", symbol="BTC", name="Bitcoin", 
                current_price=50000.0, price_change_percentage_24h=5.0,
                total_volume=1000000, category=TokenCategory.LAYER1
            ),
            TokenData(
                id="ETHUSDT", symbol="ETH", name="Ethereum", 
                current_price=3000.0, price_change_percentage_24h=-2.0,
                total_volume=500000, category=TokenCategory.LAYER1
            ),
            TokenData(
                id="DOGEUSDT", symbol="DOGE", name="Dogecoin", 
                current_price=0.1, price_change_percentage_24h=10.0,
                total_volume=200000, category=TokenCategory.MEME
            )
        ]
        self.analyzer = CryptoAnalyzer()

    def test_token_validation(self):
        """Data Class (Pydantic) doğrulama testi"""
        # Sembol otomatik büyük harf olmalı
        token = TokenData(id="test", symbol="btc", name="test", current_price=10)
        self.assertEqual(token.symbol, "BTC")
        
        # Negatif fiyat hatası vermeli
        with self.assertRaises(ValueError):
            TokenData(id="test", symbol="X", name="X", current_price=-5)

    def test_analysis_logic(self):
        """Analiz motoru testi"""
        result = self.analyzer.analyze_trend(self.sample_tokens)
        
        # En çok kazanan DOGE olmalı (%10)
        self.assertEqual(result['top_gainers'][0]['symbol'], "DOGE")
        
        # En çok kaybeden ETH olmalı (-%2)
        self.assertEqual(result['top_losers'][0]['symbol'], "ETH")
        
        # Toplam token sayısı 3 olmalı
        self.assertEqual(result['total_tokens'], 3)

if __name__ == '__main__':
    print(">>> Running Unit Tests for Crypto Analytics System...")
    unittest.main()