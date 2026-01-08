# Auth0 OAuth Configuration for Embedding Agent

## Overview

The embedding agent now uses OAuth 2.0 authentication via Auth0 Machine-to-Machine (M2M) application to securely call the AISearch API with Bearer tokens.

## Auth0 M2M Application Setup

### 1. Create Machine-to-Machine Application in Auth0

1. Log in to your [Auth0 Dashboard](https://manage.auth0.com/)
2. Navigate to **Applications** → **Applications**
3. Click **Create Application**
4. Enter a name (e.g., "Cocktails Embedding Agent M2M")
5. Select **Machine to Machine Applications**
6. Click **Create**

### 2. Authorize the Application to Access Your API

1. After creation, you'll be prompted to authorize an API
2. Select your target API (the one that handles embeddings)
3. Under **Permissions**, select the following scope:
   - `write:embeddings`
4. Click **Authorize**

### 3. Get Application Credentials

1. In your M2M application settings, go to the **Settings** tab
2. Note the following values:
   - **Domain** (e.g., `your-tenant.auth0.com`)
   - **Client ID**
   - **Client Secret**
3. Also note your **API Identifier** (found in APIs section)

### 4. Configure Environment Variables

Create or update your `.env` file with the following:

```bash
# Auth0 M2M Configuration
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your_client_id_here
AUTH0_CLIENT_SECRET=your_client_secret_here
AUTH0_AUDIENCE=https://your-api-identifier
AUTH0_SCOPE=write:embeddings

# AISearch API Configuration
AISEARCH_API_BASE_URL=https://your-api.example.com
AISEARCH_API_TIMEOUT_SECONDS=30
```

> **Security Note**: Never commit `.env` files containing secrets to version control. Use `.env.example` as a template.

## Implementation Details

### Components Added

1. **Auth0Options** (`domain/config/auth0_options.py`)
   - Configuration class for Auth0 M2M settings
   - Validates required environment variables

2. **Auth0TokenProvider** (`infrastructure/clients/auth0/auth0_token_provider.py`)
   - Handles OAuth 2.0 client credentials flow
   - Caches access tokens and automatically refreshes before expiry
   - Thread-safe token acquisition with asyncio locks

3. **Updated AISearchClient** (`infrastructure/clients/aisearch_api/aisearch_client.py`)
   - Injects Auth0TokenProvider
   - Adds Bearer token to all API requests
   - Handles 401 (Unauthorized) and 403 (Forbidden) responses

### How It Works

1. **Token Acquisition**: On first API call, the provider requests an access token from Auth0 using client credentials flow
2. **Token Caching**: The token is cached in memory with its expiration time
3. **Automatic Refresh**: Tokens are automatically refreshed 60 seconds before expiry
4. **API Authorization**: Each request to AISearch API includes `Authorization: Bearer <token>` header
5. **Scope Validation**: Auth0 ensures the token has `write:embeddings` scope before allowing API access

### Security Features

- ✅ **OAuth 2.0 Client Credentials Flow**: Industry-standard M2M authentication
- ✅ **Token Caching**: Reduces Auth0 API calls and improves performance
- ✅ **Automatic Refresh**: No manual token management required
- ✅ **Scope-Based Authorization**: Fine-grained permissions with `write:embeddings` scope
- ✅ **Thread-Safe**: Async locks prevent race conditions during token refresh

## Testing

To test the Auth0 integration:

```bash
# Ensure environment variables are set
source .env

# Run the embedding agent
poetry run cocktails-embedding-agent
```

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Verify `AUTH0_CLIENT_ID` and `AUTH0_CLIENT_SECRET` are correct
- Check that the M2M application is authorized to access your API

**403 Forbidden**
- Ensure the `write:embeddings` scope is granted to the M2M application
- Verify `AUTH0_AUDIENCE` matches your API identifier exactly

**Token Fetch Errors**
- Confirm `AUTH0_DOMAIN` is correct (no https:// prefix)
- Check network connectivity to Auth0
- Review application logs for detailed error messages

## Dependencies

- **authlib** (>=1.4.0): OAuth 2.0 client library with excellent Auth0 support
- **httpx**: Async HTTP client for API requests

## Additional Resources

- [Auth0 Machine-to-Machine Flow Documentation](https://auth0.com/docs/get-started/authentication-and-authorization-flow/client-credentials-flow)
- [Auth0 APIs Documentation](https://auth0.com/docs/get-started/apis)
- [Authlib Documentation](https://docs.authlib.org/)
