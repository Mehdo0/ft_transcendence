<script lang="ts">
	import LegalPage from '$lib/components/LegalPage.svelte';
</script>

<svelte:head>
	<title>Privacy Policy — Draw Meter</title>
</svelte:head>

<LegalPage title="Privacy Policy" updated="June 8, 2026">
	<p class="mb-8 text-xl font-semibold">
		Draw Meter is a non-commercial project built by students at 42 Lausanne. We collect the minimum
		amount of data needed to run the game and we never sell it. This page explains what we store,
		why, and what control you have over it.
	</p>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">1. Who we are</h2>
		<p class="mb-3 leading-[1.65]">
			Draw Meter is a real-time drawing game. The service is operated by the student team that
			develops it as part of the 42 curriculum. It is self-hosted and not run for profit.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">2. Data we collect</h2>
		<ul class="list-disc pl-6 leading-[1.65]">
			<li class="mb-2">
				<strong>Account data:</strong> your username, your email address, and your password. The password
				is never stored in clear text — it is hashed and salted before being saved.
			</li>
			<li class="mb-2">
				<strong>Gameplay data:</strong> your Elo rating and the results of the matches you play, so we
				can build the leaderboard.
			</li>
			<li class="mb-2">
				<strong>Drawings:</strong> the images you draw during a match are sent to our AI classifier to
				be scored in real time (see section 4).
			</li>
			<li class="mb-2">
				<strong>Technical data:</strong> a single session cookie used to keep you logged in (see section
				5).
			</li>
		</ul>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">3. How we use your data</h2>
		<p class="mb-3 leading-[1.65]">We use the data above only to:</p>
		<ul class="list-disc pl-6 leading-[1.65]">
			<li class="mb-2">authenticate you and keep your session active;</li>
			<li class="mb-2">match you with opponents and run games;</li>
			<li class="mb-2">compute your ranking and display the leaderboard.</li>
		</ul>
		<p class="mb-3 leading-[1.65]">
			We do not use your data for advertising, profiling, or automated decisions about you.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">4. The AI classifier</h2>
		<p class="mb-3 leading-[1.65]">
			While you draw, your drawing is sent to an on-device image classifier (a neural network) that
			estimates how closely it matches the target word. This happens in real time to drive the game
			and the recognition meter. Drawings are processed for scoring and are not retained as a
			long-term archive of your activity.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">5. Cookies</h2>
		<p class="mb-3 leading-[1.65]">
			We use one strictly necessary cookie: an <code
				class="border-2 border-ink bg-bg-alt px-1 text-sm">httpOnly</code
			> authentication cookie that stores your session token. It cannot be read by JavaScript and is only
			sent back to our own server. We do not use tracking, analytics, or third-party advertising cookies.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">6. Sharing</h2>
		<p class="mb-3 leading-[1.65]">
			We do not share, sell, or rent your personal data to third parties. Your username and Elo are
			visible to other players on the public leaderboard — that is the only information exposed to
			other users.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">7. Retention</h2>
		<p class="mb-3 leading-[1.65]">
			We keep your account data for as long as your account exists. If your account is deleted, the
			associated personal data is removed. Live match state is held in memory only and is discarded
			when a game ends or the server restarts.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">8. Your rights</h2>
		<p class="mb-3 leading-[1.65]">
			Under applicable Swiss and European data-protection law, you may request access to, correction
			of, or deletion of your personal data. To exercise these rights, contact the team (section
			10).
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">9. Security</h2>
		<p class="mb-3 leading-[1.65]">
			All external connections use HTTPS. Passwords are hashed and salted. Authentication relies on
			signed, server-side session tokens. No system is perfectly secure, but we apply these
			safeguards by default.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">10. Contact</h2>
		<p class="mb-3 leading-[1.65]">
			For any question about this policy or your data, reach the team through the project repository
			or your 42 Lausanne contact.
		</p>
	</section>
</LegalPage>
