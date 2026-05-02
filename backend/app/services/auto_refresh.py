"""
Automated Refresh System
Implements Vellum's approach: scheduled updates and real-time data refresh
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import json
from .multi_source_fetcher import MultiSourceFetcher
from .benchmark_fetcher import BenchmarkFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoRefreshService:
    """
    Automated refresh service for keeping leaderboard data up-to-date
    Similar to Vellum's continuous update system
    """
    
    def __init__(
        self,
        refresh_interval_hours: int = 24,
        enable_multi_source: bool = True
    ):
        """
        Initialize auto-refresh service
        
        Args:
            refresh_interval_hours: Hours between automatic refreshes
            enable_multi_source: Use multi-source fetching (Vellum approach)
        """
        self.refresh_interval = timedelta(hours=refresh_interval_hours)
        self.enable_multi_source = enable_multi_source
        self.last_refresh = None
        self.is_running = False
        
        # Initialize fetchers
        self.multi_source_fetcher = MultiSourceFetcher() if enable_multi_source else None
        self.benchmark_fetcher = BenchmarkFetcher()
        
        # Refresh status
        self.status = {
            'last_refresh': None,
            'next_refresh': None,
            'models_updated': 0,
            'status': 'idle',
            'errors': []
        }
    
    async def start(self):
        """Start the auto-refresh service"""
        if self.is_running:
            logger.warning("Auto-refresh service is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting auto-refresh service (interval: {self.refresh_interval})")
        
        # Run initial refresh
        await self.refresh_data()
        
        # Schedule periodic refreshes
        while self.is_running:
            await asyncio.sleep(self.refresh_interval.total_seconds())
            if self.is_running:
                await self.refresh_data()
    
    async def stop(self):
        """Stop the auto-refresh service"""
        logger.info("Stopping auto-refresh service")
        self.is_running = False
        self.status['status'] = 'stopped'
    
    async def refresh_data(self):
        """
        Refresh all model data from sources
        Implements Vellum's multi-source validation approach
        """
        logger.info("=" * 60)
        logger.info("Starting data refresh...")
        logger.info("=" * 60)
        
        self.status['status'] = 'refreshing'
        self.status['errors'] = []
        start_time = datetime.utcnow()
        
        try:
            if self.enable_multi_source and self.multi_source_fetcher:
                # Use multi-source fetching with live HuggingFace data
                logger.info("Using multi-source fetching with live HuggingFace API")
                models = self.multi_source_fetcher.fetch_all_models()
                logger.info(f"✓ Successfully fetched {len(models)} models from multiple sources")
            else:
                # Fallback to benchmark cache
                logger.info("Using benchmark data from cache (real data)")
                models = self.benchmark_fetcher.fetch_and_process_models()
                logger.info(f"✓ Successfully refreshed {len(models)} models")
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
        await self.refresh_data()


# Global instance
_auto_refresh_service: Optional[AutoRefreshService] = None


def get_auto_refresh_service() -> AutoRefreshService:
    """Get or create the global auto-refresh service"""
    global _auto_refresh_service
    if _auto_refresh_service is None:
        _auto_refresh_service = AutoRefreshService(
            refresh_interval_hours=24,  # Daily refresh
            enable_multi_source=True    # Use Vellum approach
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
            refresh_interval_hours=24,
            enable_multi_source=True
        )
        
        # Run one refresh
        await service.refresh_data()
        
        # Check status
        status = service.get_status()
        print(f"Status: {status}")
    
    asyncio.run(main())

# Made with Bob
