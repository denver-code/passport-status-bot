#!/usr/bin/env python3
"""
Test script to verify Pydantic v2 configuration is working correctly.
"""

import os
import sys

# Add the bot package to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_pydantic_v2() -> bool:
    """Test Pydantic v2 configuration."""
    try:
        # Test basic Pydantic v2 imports
        from pydantic import BaseModel, Field, field_validator
        from pydantic_settings import BaseSettings, SettingsConfigDict

        print("✅ Pydantic v2 imports successful")

        # Test field validator syntax
        class TestModel(BaseModel):
            name: str = Field(..., pattern=r"^[A-Za-z]+$")
            age: int = Field(gt=0)

            @field_validator("name")
            @classmethod
            def validate_name(cls, v: str) -> str:
                if len(v) < 2:
                    raise ValueError("Name too short")
                return v

        # Test model creation
        test_instance = TestModel(name="John", age=25)
        print(f"✅ Test model created: {test_instance}")

        # Test settings model
        class TestSettings(BaseSettings):
            debug: bool = Field(default=False)
            api_key: str = Field(default="test")

            model_config = SettingsConfigDict(env_prefix="TEST_", case_sensitive=False)

        settings = TestSettings()
        print(f"✅ Test settings created: debug={settings.debug}")

        print("\n🎉 All Pydantic v2 tests passed!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install pydantic pydantic-settings")
        return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_bot_config() -> bool:
    """Test bot configuration specifically."""
    try:
        # Set minimal environment for testing
        os.environ["TOKEN"] = "test_token_" + "0" * 40  # 45+ chars
        os.environ["ADMIN_ID"] = "123456789"

        from pydantic import SecretStr

        from bot.core.config import Settings

        # Test settings creation with required arguments
        settings = Settings(
            TOKEN=SecretStr(os.environ["TOKEN"]), ADMIN_ID=os.environ["ADMIN_ID"]
        )
        print("✅ Bot settings loaded successfully")
        print(f"   - Admin ID: {settings.ADMIN_ID}")
        print(f"   - Database URL: {settings.DATABASE_URL}")
        print(f"   - Debug mode: {settings.DEBUG}")

        return True
    except ImportError as e:
        print(f"❌ Cannot test bot config - missing dependencies: {e}")
        return False
    except Exception as e:
        print(f"❌ Bot configuration error: {e}")
        return False


if __name__ == "__main__":
    print("🔍 Testing Pydantic v2 Configuration\n")

    # Test basic Pydantic v2 functionality
    pydantic_ok = test_pydantic_v2()

    print("\n" + "=" * 50)

    # Test bot-specific configuration
    if pydantic_ok:
        print("🔍 Testing Bot Configuration\n")
        config_ok = test_bot_config()
    else:
        config_ok = False
        print("⏭️ Skipping bot configuration test due to import errors")

    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"   Pydantic v2 basic functionality: {'✅' if pydantic_ok else '❌'}")
    print(f"   Bot configuration: {'✅' if config_ok else '❌'}")

    if pydantic_ok and config_ok:
        print("\n🎉 All tests passed! Your Pydantic v2 migration is complete.")
    elif pydantic_ok:
        print(
            "\n⚠️ Pydantic v2 is working, but bot config needs dependencies installed."
        )
    else:
        print("\n❌ Please install dependencies to complete the migration.")
