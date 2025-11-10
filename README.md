# Stygian Relay

A powerful and customizable Discord bot for forwarding messages between channels with advanced filtering and logging capabilities. This bot is currently a work in progress.

## Current State

This bot is in active development. The core functionality of message forwarding, including message listening, rule processing, and message dispatching based on configured rules, is now implemented. A setup wizard guides you through the initial configuration. While the core forwarding is functional, some advanced features are still under development, and you may encounter bugs.

## How to Use Stygian Relay

Stygian Relay is designed to help you automate message forwarding within your Discord server. Here's how to get started and manage your forwarding rules:

### 🚀 Getting Started

### ⚙️ Commands

All bot commands start with `/forward`.

*   **`/forward setup`**:
    Initiates an interactive setup wizard to guide you through configuring new message forwarding rules. This process includes:
    1.  **Permission Check:** The bot verifies it has all necessary Discord permissions.
    2.  **Log Channel:** You'll select a dedicated channel for the bot to send logs, errors, and important notifications.
    3.  **First Forwarding Rule:** You'll create your initial rule by specifying a source channel (where messages come from) and a destination channel (where messages are sent).

*   **`/forward edit`**:
    Access an interactive interface to view and modify your existing forwarding rules. You can adjust rule names, change source or destination channels, toggle activation status, and customize formatting options.

*   **`/forward help`**:
    Provides a comprehensive overview of the bot's features and commands directly within Discord. Use this command for quick reference and assistance.

### ✨ Core Features

*   **Cross-channel Message Forwarding**: Automatically forward messages between any two channels, even across different servers.
*   **Advanced Filtering**: Control which messages are forwarded based on content, message type (text, media, links, embeds, files, stickers), and message length. (Further advanced filtering like author/role is Planned).
*   **Customizable Prefixes**: Set a unique command prefix for the bot in each server. (Planned)
*   **Database Integration**: All per-guild settings and rules are securely stored in a database.
*   **Extensible Design**: The bot's architecture allows for easy addition of new functionalities and extensions.
*   **Comprehensive Logging**: Detailed logging with optional email notifications for critical errors. (Planned)

### 🔒 Required Permissions

For Stygian Relay to function optimally, ensure it has the following Discord permissions. The setup wizard will prompt you if any are missing.

*   **Basic Permissions (Required for Core Functionality)** *Not all features are implemented yet*:
    *   **View Channels**: To list and access channels for forwarding.
    *   **Send Messages**: To post forwarded messages and command responses.
    *   **Read Message History**: To retrieve messages from source channels for forwarding.
    *   **Attach Files**: To forward messages containing file attachments.
    *   **Embed Links**: To correctly display rich embeds in forwarded messages.

*   **Advanced Permissions (Recommended for Enhanced Experience)** *Features not implemented yet*:
    *   **Manage Webhooks**: Enables more seamless and customizable message forwarding, allowing the bot to send messages with custom names and avatars.
    *   **Manage Messages**: For features like deleting original messages after forwarding.
    *   **Add Reactions**: For interactive features and user feedback.

*   **User Permissions** *Features not implemented yet*:
    *   The user initiating the `/forward setup` command must possess the "Manage Server" permission.

## Dependencies

The project's dependencies are listed in the `requirements.txt` file.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
