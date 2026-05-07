"""
Automated Refresh System
Monthly refresh schedule for leaderboard data
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import json
from .multi_provider_fetcher import MultiProviderFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoRefreshService:
    """
    Automated refresh service for keeping leaderboard data up-to-date
    Refreshes data monthly (30 days)
    """
    
    def __init__(
        self,
        refresh_interval_days: int = 30,
        enable_multi_source: bool = True
    ):
        """
        Initialize auto-refresh service
        
        Args:
            refresh_interval_days: Days between automatic refreshes (default: 30)
            enable_multi_source: Use multi-source fetching (Vellum approach)
        """
        self.refresh_interval = timedelta(days=refresh_interval_days)
        self.enable_multi_source = enable_multi_source
        self.last_refresh = None
        self.is_running = False
        
        # Initialize fetcher
        self.fetcher = MultiProviderFetcher(
            include_huggingface=True,
            include_lmsys=True,
            include_gemini=False,
            include_claude=False
        )
        
        # Refresh status
        self.status = {
            'last_refresh': None,
            'next_refresh': None,
            'models_updated': 0,
            'status': 'idle',
            'refresh_reason': None,
            'errors': []
        }
    
    async def start(self):
        """Start the auto-refresh service"""
        if self.is_running:
            logger.warning("Auto-refresh service is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting auto-refresh service")
        logger.info(f"  - Refresh interval: {self.refresh_interval.days} days")
        
        # Run initial refresh
        await self.refresh_data(reason="initial_startup")
        
        # Schedule monthly refreshes
        while self.is_running:
            await asyncio.sleep(self.refresh_interval.total_seconds())
            if self.is_running:
                await self.refresh_data(reason="scheduled_monthly")
    
    async def stop(self):
        """Stop the auto-refresh service"""
        logger.info("Stopping auto-refresh service")
        self.is_running = False
        self.status['status'] = 'stopped'
    
    async def refresh_data(self, reason: str = "manual"):
        """
        Refresh all model data from sources
        Implements Vellum's multi-source validation approach
        
        Args:
            reason: Reason for refresh (for logging)
        """
        logger.info("=" * 60)
        logger.info(f"Starting data refresh (reason: {reason})...")
        logger.info("=" * 60)
        
        self.status['status'] = 'refreshing'
        self.status['refresh_reason'] = reason
        self.status['errors'] = []
        start_time = datetime.utcnow()
        
        try:
            # Use multi-provider fetching with live data
            logger.info("Fetching live data from HuggingFace and LMSYS Arena")
            models = self.fetcher.fetch_all_models()
            logger.info(f"✓ Successfully fetched {len(models)} models from live APIs")
            self.status['models_updated'] = len(models)
            
            # Update status
            self.last_refresh = datetime.utcnow()
            self.status['last_refresh'] = self.last_refresh.isoformat()
            self.status['next_refresh'] = (
                self.last_refresh + self.refresh_interval
            ).isoformat()
            self.status['status'] = 'success'
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"✓ Refresh completed in {duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"✗ Refresh failed: {e}")
            self.status['status'] = 'error'
            self.status['errors'].append(str(e))
            raise
        
        finally:
            logger.info("=" * 60)
    
    def _save_cache(self, data: dict):
        """Save data to cache file"""
        cache_file = "data/multi_source_cache.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"✓ Cache saved to {cache_file}")
        except Exception as e:
            logger.error(f"✗ Failed to save cache: {e}")
            raise
    
    def get_status(self) -> dict:
        """Get current refresh status"""
        return self.status.copy()
    
    def should_refresh(self) -> bool:
        """Check if data should be refreshed"""
        if not self.last_refresh:
            return True
        
        time_since_refresh = datetime.utcnow() - self.last_refresh
        return time_since_refresh >= self.refresh_interval
    
    async def force_refresh(self):
        """Force an immediate refresh"""
        logger.info("Force refresh requested")
        await self.refresh_data(reason="manual_force")


# Global instance
_auto_refresh_service: Optional[AutoRefreshService] = None


def get_auto_refresh_service() -> AutoRefreshService:
    """Get or create the global auto-refresh service"""
    global _auto_refresh_service
    if _auto_refresh_service is None:
        _auto_refresh_service = AutoRefreshService(
            refresh_interval_days=30,       # Monthly refresh
            enable_multi_source=True        # Use Vellum approach
        )
    return _auto_refresh_service


async def start_auto_refresh():
    """Start the auto-refresh service"""
    service = get_auto_refresh_service()
    await service.start()


async def stop_auto_refresh():
    """Stop the auto-refresh service"""
    service = get_auto_refresh_service()
    await service.stop()


# Example usage
if __name__ == "__main__":
    async def main():
        service = AutoRefreshService(
            refresh_interval_days=30,
            enable_multi_source=True
        )
        
        # Run one refresh
        await service.refresh_data()
        
        # Check status
        status = service.get_status()
        print(f"Status: {status}")
    
    asyncio.run(main())

# Made with Bob
