<script lang="ts">
    import { goto } from '$app/navigation';
    import { resolve } from '$app/paths';
    import { registerUser, login, hashPassword } from '$lib/api';

    type Errors = {
        username?: string;
        email?: string;
        password?: string;
        confirmPassword?: string;
    };

    let username = $state('');
    let email = $state('');
    let password = $state('');
    let confirmPassword = $state('');
    let errors = $state<Errors>({});
    let serverError = $state<string | null>(null);
    let loading = $state(false);

    const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    function validate(): boolean {
        const next: Errors = {};
        if (!username.trim()) next.username = 'Username is required.';
        if (!email.trim()) next.email = 'Email is required.';
        else if (!EMAIL_RE.test(email.trim())) next.email = 'Invalid email address.';
        if (!password) next.password = 'Password is required.';
        if (!confirmPassword) next.confirmPassword = 'Confirmation is required.';
        else if (password !== confirmPassword)
            next.confirmPassword = 'Passwords do not match.';
        errors = next;
        return Object.keys(next).length === 0;
    }

    async function handleSubmit(e: Event) {
        e.preventDefault();
        serverError = null;
        if (!validate()) return;

        loading = true;
        try {
            const hashed_password = await hashPassword(password)
            console.log(hashed_password)
            const reg = await registerUser(username.trim(), email.trim(), hashed_password);
            if (!reg.ok) {
                if (reg.status === 406) serverError = 'This username is already taken.';
                else serverError = 'Registration failed, please try again.';
                return;
            }

            const log = await login(username.trim(), hashed_password);
            if (!log.ok) {
                serverError = 'Account created, but automatic login failed. Please go to the login page.';
                return;
            }

            await goto(resolve('/'));
        } finally {
            loading = false;
        }
    }
</script>

<svelte:head>
    <title>Register - Ping Pong Hub</title>
</svelte:head>

<div class="auth-container">
    <main class="auth-card">
        <h1 class="title">Register</h1>
        <p class="subtitle">Join the competition</p>

        {#if serverError}
            <div class="server-error" role="alert">{serverError}</div>
        {/if}

        <form onsubmit={handleSubmit} novalidate>
            <div class="field">
                <label for="username">Username</label>
                <input
                    id="username"
                    type="text"
                    autocomplete="username"
                    bind:value={username}
                    aria-invalid={!!errors.username}
                    aria-describedby={errors.username ? 'username-err' : undefined}
                    disabled={loading}
                    placeholder="e.g., mehdi ce gros enculer"
                />
                {#if errors.username}
                    <span class="field-error" id="username-err" aria-live="polite">{errors.username}</span>
                {/if}
            </div>

            <div class="field">
                <label for="email">Email</label>
                <input
                    id="email"
                    type="email"
                    autocomplete="email"
                    bind:value={email}
                    aria-invalid={!!errors.email}
                    aria-describedby={errors.email ? 'email-err' : undefined}
                    disabled={loading}
                    placeholder="e.g., player@email.com"
                />
                {#if errors.email}
                    <span class="field-error" id="email-err" aria-live="polite">{errors.email}</span>
                {/if}
            </div>

            <div class="field">
                <label for="password">Password</label>
                <input
                    id="password"
                    type="password"
                    autocomplete="new-password"
                    bind:value={password}
                    aria-invalid={!!errors.password}
                    aria-describedby={errors.password ? 'password-err' : undefined}
                    disabled={loading}
                    placeholder="••••••••"
                />
                {#if errors.password}
                    <span class="field-error" id="password-err" aria-live="polite">{errors.password}</span>
                {/if}
            </div>

            <div class="field">
                <label for="confirm">Confirm Password</label>
                <input
                    id="confirm"
                    type="password"
                    autocomplete="new-password"
                    bind:value={confirmPassword}
                    aria-invalid={!!errors.confirmPassword}
                    aria-describedby={errors.confirmPassword ? 'confirm-err' : undefined}
                    disabled={loading}
                    placeholder="••••••••"
                />
                {#if errors.confirmPassword}
                    <span class="field-error" id="confirm-err" aria-live="polite">{errors.confirmPassword}</span>
                {/if}
            </div>

            <button type="submit" class="menu-btn primary" disabled={loading}>
                {loading ? 'Registering...' : 'Register'}
            </button>
        </form>

        <p class="alt">
            Already have an account? <a href={resolve('/account/login')}>Log in</a>
        </p>
    </main>
</div>

<style>
    /* Centers the card exactly like the Lobby and Dashboard pages */
    .auth-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 70vh;
        padding: 2rem;
    }

    /* The signature white card with a soft shadow */
    .auth-card {
        background-color: white;
        width: 100%;
        max-width: 450px;
        padding: 3rem;
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        box-sizing: border-box;
    }

    .title {
        color: blueviolet;
        margin: 0;
        font-size: 2.2rem;
        text-align: center;
    }

    .subtitle {
        text-align: center;
        color: #666;
        margin-top: 5px;
        margin-bottom: 2rem;
        font-size: 1.05rem;
    }

    form {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
    }

    .field {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }

    label {
        font-size: 0.95rem;
        font-weight: 600;
        color: #444;
    }

    input {
        padding: 12px 15px;
        border: 2px solid #ddd;
        border-radius: 8px;
        font-size: 1rem;
        background: #fafafa;
        font-family: inherit;
        transition: all 0.2s ease;
    }

    input:focus {
        outline: none;
        border-color: blueviolet;
        background: white;
        box-shadow: 0 0 0 3px rgba(138, 43, 226, 0.1);
    }

    input[aria-invalid='true'] {
        border-color: #e74c3c;
        background: #fdf5f5;
    }

    input:disabled {
        background: #eee;
        color: #999;
        cursor: not-allowed;
        border-color: #ddd;
    }

    .field-error {
        color: #e74c3c;
        font-size: 0.85rem;
        font-weight: 500;
    }

    .server-error {
        background: #fee;
        color: red;
        padding: 1rem;
        border-radius: 6px;
        margin-bottom: 1.5rem;
        font-size: 0.95rem;
        font-weight: bold;
        text-align: center;
    }

    /* Matches the primary buttons from your other pages */
    .menu-btn.primary {
        margin-top: 1rem;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 55px;
        font-size: 1.1rem;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        font-family: inherit;
        background-color: blueviolet;
        color: white;
        border: none;
    }

    .menu-btn.primary:hover:not(:disabled) {
        background-color: #7a1cd1;
        transform: translateY(-2px);
    }

    .menu-btn.primary:disabled {
        background-color: #a074d6;
        cursor: not-allowed;
        transform: none;
    }

    .alt {
        margin-top: 2rem;
        font-size: 0.95rem;
        text-align: center;
        color: #666;
    }

    .alt a {
        color: blueviolet;
        font-weight: bold;
        text-decoration: none;
        transition: color 0.2s;
    }

    .alt a:hover {
        color: #7a1cd1;
        text-decoration: underline;
    }
</style>
