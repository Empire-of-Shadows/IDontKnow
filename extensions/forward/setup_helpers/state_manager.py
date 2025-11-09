"""
Manages setup state across multiple guilds and sessions.
"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime, timedelta

from database import db_core
from ..models.setup_state import SetupState


class SetupStateManager:
    """Manages active setup sessions across the bot."""

    def __init__(self):
        self.active_sessions: Dict[int, SetupState] = {}  # guild_id -> SetupState
        self._lock = asyncio.Lock()

    async def create_session(self, guild_id: int, user_id: int) -> SetupState:
        """Create a new setup session for a guild."""
        async with self._lock:
            # Check for existing session
            if guild_id in self.active_sessions:
                existing = self.active_sessions[guild_id]
                if not existing.is_expired():
                    return existing
                # Remove expired session
                await self.cleanup_session(guild_id)

            # Create new session
            session = SetupState(guild_id, user_id)
            self.active_sessions[guild_id] = session

            # Todo: Save session to database for persistence across restarts
            # await self._save_session_to_db(session)

            return session

    async def get_session(self, guild_id: int) -> Optional[SetupState]:
        """Get an active setup session for a guild."""
        async with self._lock:
            session = self.active_sessions.get(guild_id)
            if session and session.is_expired():
                await self.cleanup_session(guild_id)
                return None
            return session

    async def update_session(self, guild_id: int, updates: Dict[str, any]) -> bool:
        """Update a setup session with new data."""
        async with self._lock:
            session = self.active_sessions.get(guild_id)
            if not session:
                return False

            # Apply updates
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            session.update_activity()

            # Todo: Update session in database
            # await self._save_session_to_db(session)

            return True

    async def cleanup_session(self, guild_id: int) -> bool:
        """Clean up a setup session."""
        async with self._lock:
            if guild_id in self.active_sessions:
                # Todo: Save final state to database before cleanup
                # session = self.active_sessions[guild_id]
                # await self._save_session_to_db(session)

                del self.active_sessions[guild_id]
                return True
            return False

    async def cleanup_expired_sessions(self):
        """Clean up all expired sessions."""
        async with self._lock:
            expired_guilds = []
            for guild_id, session in self.active_sessions.items():
                if session.is_expired():
                    expired_guilds.append(guild_id)

            for guild_id in expired_guilds:
                # Todo: Save expired session state for potential resume
                del self.active_sessions[guild_id]

            if expired_guilds:
                print(f"Cleaned up {len(expired_guilds)} expired setup sessions")

    async def get_session_count(self) -> int:
        """Get number of active setup sessions."""
        async with self._lock:
            return len(self.active_sessions)

    # Todo: Implement database persistence methods
    async def _save_session_to_db(self, session: SetupState):
        """Save session state to database for persistence."""
        # This will allow resuming setups after bot restarts
        pass

    async def _load_session_from_db(self, guild_id: int) -> Optional[SetupState]:
        """Load session state from database."""
        # This will allow resuming setups after bot restarts
        pass


# Global state manager instance
state_manager = SetupStateManager()