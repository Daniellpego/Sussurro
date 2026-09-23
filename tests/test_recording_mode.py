from unittest.mock import MagicMock

from pynput import keyboard
from PySide6.QtCore import QCoreApplication

from sussurro.hotkey.listener import PushToTalkListener
from sussurro.storage.config import Config


def test_config_recording_mode_defaults():
    cfg = Config()
    assert cfg.recording_mode == "push_to_talk"
    cfg.recording_mode = "toggle"
    assert cfg.recording_mode == "toggle"


def test_listener_push_to_talk_behavior():
    _ = QCoreApplication.instance() or QCoreApplication([])
    listener = PushToTalkListener(mode="push_to_talk")

    pressed_mock = MagicMock()
    released_mock = MagicMock()
    cancelled_mock = MagicMock()
    listener.pressed.connect(pressed_mock)
    listener.released.connect(released_mock)
    listener.cancelled.connect(cancelled_mock)

    # Press Ctrl, then Win -> should emit pressed
    listener._on_press(keyboard.Key.ctrl)
    assert not pressed_mock.called
    listener._on_press(keyboard.Key.cmd)
    assert pressed_mock.called
    assert listener._active

    # Release Win -> should emit released
    listener._on_release(keyboard.Key.cmd)
    assert released_mock.called
    assert not listener._active


def test_listener_toggle_mode_behavior():
    _ = QCoreApplication.instance() or QCoreApplication([])
    listener = PushToTalkListener(mode="toggle")

    pressed_mock = MagicMock()
    released_mock = MagicMock()
    listener.pressed.connect(pressed_mock)
    listener.released.connect(released_mock)

    # First press of Ctrl + Win
    listener._on_press(keyboard.Key.ctrl)
    listener._on_press(keyboard.Key.cmd)
    assert pressed_mock.called
    assert listener._active

    # Releasing keys in toggle mode does NOT deactivate
    listener._on_release(keyboard.Key.cmd)
    listener._on_release(keyboard.Key.ctrl)
    assert not released_mock.called
    assert listener._active

    # Wait debounce interval
    listener._last_toggle_time -= 0.5

    # Second press of Ctrl + Win -> should toggle OFF and emit released
    listener._on_press(keyboard.Key.ctrl)
    listener._on_press(keyboard.Key.cmd)
    assert released_mock.called
    assert not listener._active


def test_listener_set_mode():
    listener = PushToTalkListener(mode="push_to_talk")
    assert listener.mode == "push_to_talk"
    listener.set_mode("toggle")
    assert listener.mode == "toggle"
