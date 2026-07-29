---
name: orcanos-login
description: Build Orcanos login screens with QW_Login API integration, design, and reusable patterns
---

# Orcanos Login Screen Skill

Build a production-ready login screen for any Orcanos-connected app using the QW_Login API.

## What this covers

- **API contract** — QW_Login endpoint, Basic auth encoding, response shape, error handling
- **Design system** — colors, typography, spacing (Orcanos standard design tokens)
- **Form UX** — username/password fields, show/hide toggle, validation, accessibility
- **State management** — form state, loading, error handling, auth persistence
- **Copy-paste code** — ready-to-use submit handler, CSS, component structure
- **Cross-app reuse** — checklist to adapt the pattern for different projects

## How to invoke this

When building a login screen for an Orcanos app:

```
/orcanos-login — generate a login screen for my app at {baseUrl}
```

Provide:
- **Base URL** of your Orcanos instance (e.g., `https://us.orcanos.com/covaris/`)
- **Redirect/callback** — where to send the user on successful login
- **Styling** — use default design tokens or override colors/fonts

## Quick reference: QW_Login API

### Endpoint
```
POST {baseUrl}api/v2/Json/QW_Login
```

### Headers
```
Authorization: Basic {base64(username:password)}
Content-Type: application/json
```

**Never store the plaintext password.** Only store the `Authorization` header in `localStorage`.

### Request
```json
{}
```
(empty body)

### Success (HTTP 200)
```json
{
  "IsSuccess": true,
  "Data": { "UserName": "...", "UserId": "...", ... }
}
```

### Error (HTTP 401/403/500)
```json
{
  "IsSuccess": false,
  "Messages": [{ "MessageType": 2, "Text": "..." }]
}
```

**Always show a generic error message to the user.** Never echo the server's message (it may leak system details).

---

## Form structure

```
┌─────────────────────────────────────┐
│  [Logo/Title]                       │
│                                     │
│  Username                           │
│  [_____________]                    │
│                                     │
│  Password                           │
│  [_____________] [show/hide]        │
│                                     │
│  [error message] ← if any           │
│                                     │
│  [✓ Sign In]                        │
└─────────────────────────────────────┘
```

**Max width:** 400px (responsive). **Padding:** 40px desktop / 20px mobile.

---

## Implementation checklist

- [ ] Create `src/auth/Login.jsx` with form layout (see code template below)
- [ ] Add state for username, password, loading, error, showPassword
- [ ] Implement submit handler:
  - Encode `username:password` as Base64
  - POST to `{baseUrl}api/v2/Json/QW_Login` with Basic auth header
  - On success: store `Authorization` header + username in localStorage
  - On 401/403: show generic error, clear password field, stay on login
  - On network error: show "Check your connection" message
- [ ] Add CSS for form, inputs, buttons, error state
- [ ] Add password visibility toggle (show/hide icon)
- [ ] Integrate with your App.jsx:
  - Read auth from localStorage on mount
  - Show `<Login>` if no auth, show `<MainView>` if auth exists
  - Clear localStorage + redirect to login on 401 from any API call
- [ ] Test:
  - Valid credentials → success, navigate to main view
  - Invalid credentials → error message, password cleared
  - Network down → network error message
  - Empty fields → submit button disabled
  - Mobile layout → responsive, no horizontal scroll
  - Keyboard → Enter in password field submits form
  - 401 on API call → logout and redirect to login

---

## Code template

### State
```jsx
const [username, setUsername] = useState('');
const [password, setPassword] = useState('');
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);
const [showPassword, setShowPassword] = useState(false);
```

### Submit handler
```jsx
const handleSubmit = async (e) => {
  e?.preventDefault();
  if (!username.trim() || !password.trim()) return;

  setLoading(true);
  setError(null);

  try {
    const auth = btoa(`${username}:${password}`);
    const response = await fetch(`${baseUrl}api/v2/Json/QW_Login`, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });

    const data = await response.json();
    if (!data.IsSuccess) {
      setError('Login failed. Check your credentials and try again.');
      setPassword('');
      return;
    }

    // Success
    localStorage.setItem('orcanos_auth', `Basic ${auth}`);
    localStorage.setItem('orcanos_user', username);
    onSuccess?.();
  } catch (err) {
    setError('Network error. Check your connection and try again.');
    setPassword('');
  } finally {
    setLoading(false);
  }
};
```

### Form JSX (minimal)
```jsx
<form onSubmit={handleSubmit} className="login-form">
  <h1>Sign In</h1>

  <div className="form-group">
    <label htmlFor="username">Username</label>
    <input
      id="username"
      type="text"
      value={username}
      onChange={(e) => setUsername(e.target.value)}
      disabled={loading}
      autoFocus
    />
  </div>

  <div className="form-group password-field">
    <label htmlFor="password">Password</label>
    <input
      id="password"
      type={showPassword ? 'text' : 'password'}
      value={password}
      onChange={(e) => setPassword(e.target.value)}
      disabled={loading}
    />
    <button
      type="button"
      className="password-toggle"
      onClick={() => setShowPassword(!showPassword)}
      aria-label={showPassword ? 'Hide password' : 'Show password'}
    >
      {showPassword ? '👁️' : '👁️‍🗨️'}
    </button>
  </div>

  {error && (
    <div className="login-error" role="alert">
      {error}
    </div>
  )}

  <button
    type="submit"
    disabled={loading || !username.trim() || !password.trim()}
    className="login-button"
  >
    {loading ? '...' : 'Sign In'}
  </button>
</form>
```

### CSS (core)
```css
.login-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  background-color: #ffffff;
  font-family: Inter, sans-serif;
}

.login-form {
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.login-form h1 {
  font-size: 32px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 24px;
  text-align: center;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
}

.form-group input {
  padding: 12px 14px;
  font-size: 14px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-family: inherit;
}

.form-group input:focus {
  outline: none;
  border-color: #5C35A8;
  box-shadow: 0 0 0 3px rgba(92, 53, 168, 0.1);
}

.password-field {
  position: relative;
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  font-size: 18px;
}

.login-button {
  padding: 12px 20px;
  height: 44px;
  background-color: #5C35A8;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
}

.login-button:hover:not(:disabled) {
  background-color: #4a2a8a;
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-error {
  padding: 12px 14px;
  background-color: #ffebee;
  color: #D32F2F;
  border-radius: 6px;
  font-size: 14px;
  border-left: 4px solid #D32F2F;
}
```

---

## Using in your App

1. **Store auth check:**
   ```jsx
   const [auth, setAuth] = useState(null);
   
   useEffect(() => {
     const stored = localStorage.getItem('orcanos_auth');
     if (stored) setAuth(stored);
   }, []);
   ```

2. **Show/hide views:**
   ```jsx
   return auth ? <MainView auth={auth} /> : <Login onSuccess={() => setAuth(localStorage.getItem('orcanos_auth'))} />;
   ```

3. **Make API calls with auth:**
   ```jsx
   const auth = localStorage.getItem('orcanos_auth');
   fetch(url, {
     headers: { 'Authorization': auth, 'Content-Type': 'application/json' },
     // ...
   });
   ```

4. **Handle 401 responses:**
   ```jsx
   if (response.status === 401) {
     localStorage.removeItem('orcanos_auth');
     localStorage.removeItem('orcanos_user');
     window.location.href = '/';
   }
   ```

---

## Key gotchas

- ✅ **Auth is sent as a header**, not in the body. Encode `username:password` as Base64, prepend `Basic `.
- ✅ **Never store plaintext passwords.** Only store the `Authorization` header.
- ✅ **QW_Login returns `IsSuccess` boolean.** Don't try to parse or validate the `Data` object.
- ✅ **Show generic errors to users.** Never echo the server's error message.
- ✅ **Handle 401 on every API call.** When it happens, clear auth and redirect to login.
- ✅ **Clear password on error.** Never show it again to the user.
- ✅ **Test on mobile.** Password field needs show/hide toggle for usability.

---

## Cross-app checklist

When copying this pattern to a new Orcanos app:

- [ ] Replace `baseUrl` with your Orcanos instance URL
- [ ] Replace `onSuccess` callback with your navigation logic (e.g., `navigate('/home')`)
- [ ] Adjust colors/fonts if needed (recommend using design system tokens, e.g., CSS variables)
- [ ] Add your app's logo/title in the form
- [ ] Test with real credentials against your Orcanos instance
- [ ] Verify localStorage keys don't collide with other apps (consider prefixing: `myapp_auth`, `myapp_user`)
- [ ] Add logout button in main view (clears localStorage, redirects to login)
- [ ] Test 401 handling by manually clearing localStorage and making an API call
