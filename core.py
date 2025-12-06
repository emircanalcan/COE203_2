"""
=============================================================================
BACKEND MODULE - CRYPTO ANALYTICS SYSTEM
=============================================================================
Contains: Data Models, Database Connection, API Fetchers, Analysis Logic
"""
import math
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Protocol
from enum import Enum
from abc import ABC, abstractmethod

import requests
import urllib3
from pydantic import BaseModel, Field, validator
from mongoengine import (
    Document, StringField, FloatField, IntField,
    DateTimeField, EnumField, connect
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

# ============================================================================
# MODULE 1: DATA MODELS & VALIDATION (PYDANTIC)
# ============================================================================

class TokenCategory(str, Enum):
    """Enumeration for Token Categories"""
    LAYER1 = "Layer 1"
    LAYER2 = "Layer 2"
    DEFI = "DeFi"
    NFT = "NFT/Gaming"
    MEME = "Meme"
    STABLE = "Stablecoin"
    UNKNOWN = "Unknown"

class TokenData(BaseModel):
    """
    Data Transfer Object (DTO) for Token Information.
    Uses Pydantic for runtime type checking and validation.
    """
    id: str = Field(..., description="Unique Token Identifier (Symbol)")
    symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1)
    current_price: float = Field(default=0.0, ge=0)
    market_cap: float = Field(default=0.0, ge=0)
    market_cap_rank: int = Field(default=0)
    total_volume: float = Field(default=0.0, ge=0)
    price_change_24h: float = Field(default=0.0)
    price_change_percentage_24h: float = Field(default=0.0)
    circulating_supply: float = Field(default=0.0)
    total_supply: float = Field(default=0.0)
    max_supply: float = Field(default=0.0)
    last_updated: datetime = Field(default_factory=datetime.now)
    category: Optional[TokenCategory] = Field(default=TokenCategory.UNKNOWN)

    @validator('symbol')
    def symbol_uppercase(cls, value):  # pylint: disable=no-self-argument
        """Ensure symbol is always uppercase"""
        return value.upper()

    class Config:
        """Pydantic config"""
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            TokenCategory: lambda cat: cat.value
        }
        arbitrary_types_allowed = True

class HistoricalData(BaseModel):
    """Model for historical price points"""
    timestamp: datetime
    token_id: str
    price: float
    volume: float
    market_cap: float

# ============================================================================
# MODULE 2: INTERFACES & ABSTRACTIONS (OOP CORE)
# ============================================================================

class DataFetcher(Protocol):
    """
    Protocol defining the contract for any Data Fetching mechanism.
    Any class implementing this must provide these methods.
    """
    @abstractmethod
    def fetch_data(self) -> List[TokenData]:
        """Retrieves current market data"""

    @abstractmethod
    def fetch_historical(self, token_id: str, days: int) -> List[HistoricalData]:
        """Retrieves historical data"""

class BaseAnalyzer(ABC):
    """
    Abstract Base Class for Analytics Engines.
    Enforces implementation of specific analysis algorithms.
    """
    @abstractmethod
    def analyze_trend(self, data: List[TokenData]) -> Dict[str, Any]:
        """Analyze current market trends"""

    @abstractmethod
    def calculate_correlation(self, token1: str, token2: str) -> float:
        """Calculate Pearson correlation coefficient"""

# ============================================================================
# MODULE 3: API IMPLEMENTATION (INHERITANCE)
# ============================================================================
class CryptoAPIFetcher:
    """
    Parent Class: Handles low-level HTTP networking.
    Implements shared logic for all API interactions.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/91.0.4472.124 Safari/537.36'
            ),
            'Accept': 'application/json'
        })

    def _make_request(self, endpoint: str, params: dict = None) -> Any:
        """
        Executes HTTP GET request with error handling and SSL bypass.
        """
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=5, verify=False)

            if response.status_code == 200:
                return response.json()
            logger.error("API Request Failed: %s", response.status_code)
            return None
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Network Exception: %s", str(e))
            return None

class BinanceTokensFetcher(CryptoAPIFetcher, DataFetcher):
    """
    Child Class: Specific implementation for BINANCE API.
    Inherits networking capabilities from CryptoAPIFetcher.
    Implements DataFetcher protocol.
    """
    def __init__(self, limit: int = 50):
        super().__init__(base_url="https://api.binance.com/api/v3")
        self.limit = limit
        self.tokens_cache = []
        logger.info("Binance Fetcher initialized with limit=%d", limit)

    def fetch_data(self) -> List[TokenData]:
        """
        Fetches live ticker data from Binance.
        Strategy: Get all tickers -> Filter USDT -> Sort by Volume -> Slice Top N
        """
        all_tickers = self._make_request("ticker/24hr")

        if not all_tickers:
            return []

        usdt_pairs = [x for x in all_tickers if x['symbol'].endswith('USDT')]

        try:
            usdt_pairs.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
        except ValueError:
            pass

        top_n = usdt_pairs[:self.limit]

        tokens = []
        for i, item in enumerate(top_n):
            try:
                token_obj = self._parse_binance_token(item, i + 1)
                tokens.append(token_obj)
            except Exception:  # pylint: disable=broad-exception-caught
                continue

        self.tokens_cache = tokens
        return tokens

    def _parse_binance_token(self, item: Dict, rank: int) -> TokenData:
        """Helper to map raw Binance JSON to strict TokenData model"""
        symbol_full = item['symbol']
        symbol_short = symbol_full.replace('USDT', '')

        def safe_float(key):
            try:
                return float(item.get(key, 0))
            except (ValueError, TypeError):
                return 0.0

        cat = TokenCategory.UNKNOWN
        if symbol_short in ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'AVAX']:
            cat = TokenCategory.LAYER1
        elif symbol_short in ['USDT', 'USDC', 'FDUSD', 'DAI']:
            cat = TokenCategory.STABLE
        elif symbol_short in ['UNI', 'AAVE', 'CAKE']:
            cat = TokenCategory.DEFI
        elif symbol_short in ['DOGE', 'SHIB', 'PEPE']:
            cat = TokenCategory.MEME
        elif symbol_short in ['AXS', 'MANA', 'SAND']:
            cat = TokenCategory.NFT

        return TokenData(
            id=symbol_full,
            symbol=symbol_short,
            name=symbol_short,
            current_price=safe_float('lastPrice'),
            market_cap=0.0,
            market_cap_rank=rank,
            total_volume=safe_float('quoteVolume'),
            price_change_24h=safe_float('priceChange'),
            price_change_percentage_24h=safe_float('priceChangePercent'),
            circulating_supply=0.0,
            total_supply=0.0,
            max_supply=0.0,
            last_updated=datetime.now(),
            category=cat
        )

    def fetch_historical(self, token_id: str, days: int = 7) -> List[HistoricalData]:
        """Fetches historical K-Lines (Candlestick) data"""
        endpoint = "klines"
        params = {
            'symbol': token_id,
            'interval': '1d',
            'limit': days
        }

        data = self._make_request(endpoint, params)
        if not data:
            return []

        history = []
        for candle in data:
            try:
                t_stamp = datetime.fromtimestamp(candle[0] / 1000)
                close_price = float(candle[4])
                vol = float(candle[5])

                history.append(HistoricalData(
                    timestamp=t_stamp,
                    token_id=token_id,
                    price=close_price,
                    volume=vol,
                    market_cap=0.0
                ))
            except Exception:  # pylint: disable=broad-exception-caught
                continue

        return history

# ============================================================================
# MODULE 4: DATABASE LAYER (MONGOENGINE ORM)
# ============================================================================

try:
    print(">>> DB: Attempting connection to MongoDB Atlas...")
    connect(
        db='FinansTakipDB',
        host='mongodb+srv://admin:admin1234@cluster0.cdrich6.mongodb.net/?appName=Cluster0',
        alias='default'
    )
    print(">>> DB: Connection Successful.")
except Exception as e:  # pylint: disable=broad-exception-caught
    print(f">>> DB FATAL ERROR: {e}")

class TokenDocument(Document):
    """
    MongoDB Document Model for storing Token Information.
    Corresponds to 'top_tokens' collection.
    """
    meta = {
        'collection': 'top_tokens',
        'ordering': ['market_cap_rank'],
        'strict': False
    }

    token_id = StringField(required=True, unique=True)
    symbol = StringField()
    name = StringField()
    current_price = FloatField()
    market_cap = FloatField()
    market_cap_rank = IntField()
    total_volume = FloatField()
    price_change_24h = FloatField()
    price_change_percentage_24h = FloatField()

    circulating_supply = FloatField()
    total_supply = FloatField()
    max_supply = FloatField()

    last_updated = DateTimeField()
    category = EnumField(TokenCategory)

    def update_from_dto(self, data: TokenData):
        """Update document fields from Data Transfer Object"""
        self.current_price = data.current_price
        self.total_volume = data.total_volume
        self.price_change_percentage_24h = data.price_change_percentage_24h
        self.last_updated = datetime.now()
        self.save()

    @classmethod
    def from_pydantic(cls, dto: TokenData):
        """Factory method to create Document from Pydantic model"""
        return cls(
            token_id=dto.id,
            symbol=dto.symbol,
            name=dto.name,
            current_price=dto.current_price,
            market_cap=dto.market_cap,
            market_cap_rank=dto.market_cap_rank,
            total_volume=dto.total_volume,
            price_change_24h=dto.price_change_24h,
            price_change_percentage_24h=dto.price_change_percentage_24h,
            circulating_supply=dto.circulating_supply,
            total_supply=dto.total_supply,
            max_supply=dto.max_supply,
            last_updated=dto.last_updated,
            category=dto.category
        )

class HistoricalDocument(Document):
    """MongoDB Document for Historical Data"""
    meta = {
        'collection': 'historical_data',
        'indexes': ['token_id', 'timestamp'],
        'strict': False
    }

    timestamp = DateTimeField(required=True)
    token_id = StringField(required=True)
    price = FloatField(required=True)
    volume = FloatField()
    market_cap = FloatField()

# ============================================================================
# MODULE 5: ANALYTICS ENGINE
# ============================================================================
class CryptoAnalyzer(BaseAnalyzer):
    """
    Implementation of Analysis Logic.
    Calculates trends, gainers/losers, and statistical correlations.
    """

    def analyze_trend(self, data: List[TokenData]) -> Dict[str, Any]:
        """Generates a market summary report"""
        if not data:
            return {}

        try:
            sorted_desc = sorted(
                data,
                key=lambda x: x.price_change_percentage_24h or 0,
                reverse=True
            )

            top_gainers = [
                {
                    'symbol': t.symbol,
                    'price': t.current_price,
                    'change': t.price_change_percentage_24h
                }
                for t in sorted_desc[:5]
            ]

            sorted_asc = sorted(
                data,
                key=lambda x: x.price_change_percentage_24h or 0,
                reverse=False
            )

            top_losers = [
                {
                    'symbol': t.symbol,
                    'price': t.current_price,
                    'change': t.price_change_percentage_24h
                }
                for t in sorted_asc[:5]
            ]

            total_vol = sum(t.total_volume for t in data)

            return {
                'total_tokens': len(data),
                'total_volume': total_vol,
                'top_gainers': top_gainers,
                'top_losers': top_losers,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Analysis Error: %s", e)
            return {}

    def calculate_correlation(self, token1: str, token2: str) -> float:
        """
        Calculates Pearson Correlation between two assets based on historical DB data.
        """
        try:
            # pylint: disable=no-member
            docs1 = HistoricalDocument.objects(token_id=token1).limit(30)
            docs2 = HistoricalDocument.objects(token_id=token2).limit(30)

            prices1 = [d.price for d in docs1]
            prices2 = [d.price for d in docs2]

            if len(prices1) < 2 or len(prices2) < 2:
                return 0.0

            min_len = min(len(prices1), len(prices2))
            prices1 = prices1[:min_len]
            prices2 = prices2[:min_len]

            mean1 = sum(prices1) / len(prices1)
            mean2 = sum(prices2) / len(prices2)

            numerator = sum(
                (p1 - mean1) * (p2 - mean2) for p1, p2 in zip(prices1, prices2)
            )
            denominator = math.sqrt(
                sum((p - mean1)**2 for p in prices1) *
                sum((p - mean2)**2 for p in prices2)
            )

            if denominator == 0:
                return 0.0
            return numerator / denominator
        except Exception:  # pylint: disable=broad-exception-caught
            return 0.0