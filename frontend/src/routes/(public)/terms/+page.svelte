<svelte:head>
	<title>Terms of Service — Draw Meter</title>
</svelte:head>

<div class="legal-container">
	<article class="nb-card legal">
		<header class="legal-header">
			<h1>Terms of Service</h1>
			<p class="updated">Last updated: June 8, 2026</p>
		</header>

		<p class="intro">
			By creating an account or playing Draw Meter, you agree to these terms. Draw Meter is a
			non-commercial student project — please play fair and keep it friendly.
		</p>

		<section>
			<h2>1. Acceptance</h2>
			<p>
				These terms form an agreement between you and the Draw Meter team. If you do not agree with
				them, do not use the service.
			</p>
		</section>

		<section>
			<h2>2. Your account</h2>
			<p>
				You are responsible for keeping your credentials secret and for all activity under your
				account. You must provide a valid email and choose a username that is not offensive or
				impersonating someone else. One person should not create accounts to gain an unfair ranking
				advantage.
			</p>
		</section>

		<section>
			<h2>3. Fair play</h2>
			<p>You agree not to:</p>
			<ul>
				<li>
					cheat, automate drawings, or otherwise manipulate the AI scoring or the matchmaking;
				</li>
				<li>draw content that is illegal, hateful, harassing, or sexually explicit;</li>
				<li>disrupt the service, other players, or the underlying infrastructure;</li>
				<li>attempt to access accounts, data, or systems that are not yours.</li>
			</ul>
			<p>
				Surrendering, disconnecting to dodge a loss, or abusing the reconnection grace period may be
				treated as a forfeit.
			</p>
		</section>

		<section>
			<h2>4. Your content</h2>
			<p>
				The drawings you create remain yours. By submitting them during a match, you grant us the
				limited right to process them in order to run the game (scoring, displaying, and
				matchmaking). We do not claim ownership of your drawings.
			</p>
		</section>

		<section>
			<h2>5. Intellectual property</h2>
			<p>
				The Draw Meter name, code, and visual design belong to the team that built it. You may not
				copy or redistribute the service as your own without permission.
			</p>
		</section>

		<section>
			<h2>6. Availability</h2>
			<p>
				The service is provided "as is" and "as available". As a student project, it may be offline,
				reset, or changed at any time without notice. Game state is held in memory and can be lost
				on a restart.
			</p>
		</section>

		<section>
			<h2>7. Limitation of liability</h2>
			<p>
				To the extent permitted by law, the team is not liable for any indirect or incidental damage
				arising from your use of the service, including loss of data or ranking.
			</p>
		</section>

		<section>
			<h2>8. Termination</h2>
			<p>
				We may suspend or remove accounts that break these terms. You may stop using the service and
				request deletion of your account at any time.
			</p>
		</section>

		<section>
			<h2>9. Governing law</h2>
			<p>
				These terms are governed by the laws of Switzerland, without regard to conflict-of-law
				rules.
			</p>
		</section>

		<section>
			<h2>10. Changes &amp; contact</h2>
			<p>
				We may update these terms; continued use after a change means you accept the new version.
				For any question, reach the team through the project repository or your 42 Lausanne contact.
				See also our <a href="/privacy">Privacy Policy</a>.
			</p>
		</section>
	</article>
</div>

<style>
	.legal-container {
		flex: 1;
		display: flex;
		justify-content: center;
		padding: var(--space-6) 0;
	}

	.legal {
		width: 100%;
		max-width: 760px;
		box-shadow: var(--shadow-lg);
	}

	.legal-header {
		border-bottom: var(--border-lg);
		padding-bottom: var(--space-4);
		margin-bottom: var(--space-5);
	}

	.legal h1 {
		margin: 0 0 var(--space-2);
		font-size: var(--fs-3xl);
		text-transform: uppercase;
	}

	.updated {
		margin: 0;
		font-family: var(--font-mono);
		font-size: var(--fs-sm);
		color: var(--c-muted);
	}

	.intro {
		font-size: var(--fs-lg);
		font-weight: var(--fw-medium);
		margin: 0 0 var(--space-6);
	}

	section {
		margin-bottom: var(--space-6);
	}

	.legal h2 {
		font-size: var(--fs-lg);
		text-transform: uppercase;
		margin: 0 0 var(--space-3);
	}

	.legal p {
		margin: 0 0 var(--space-3);
		line-height: 1.65;
	}

	.legal ul {
		margin: 0;
		padding-left: var(--space-5);
		line-height: 1.65;
	}

	.legal li {
		margin-bottom: var(--space-2);
	}
</style>
