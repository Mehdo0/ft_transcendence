<script lang="ts">
	import LegalPage from '$lib/components/LegalPage.svelte';
</script>

<svelte:head>
	<title>Terms of Service — Draw Meter</title>
</svelte:head>

<LegalPage title="Terms of Service" updated="June 8, 2026">
	<p class="mb-8 text-xl font-semibold">
		By creating an account or playing Draw Meter, you agree to these terms. Draw Meter is a
		non-commercial student project — please play fair and keep it friendly.
	</p>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">1. Acceptance</h2>
		<p class="mb-3 leading-[1.65]">
			These terms form an agreement between you and the Draw Meter team. If you do not agree with
			them, do not use the service.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">2. Your account</h2>
		<p class="mb-3 leading-[1.65]">
			You are responsible for keeping your credentials secret and for all activity under your
			account. You must provide a valid email and choose a username that is not offensive or
			impersonating someone else. One person should not create accounts to gain an unfair ranking
			advantage.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">3. Fair play</h2>
		<p class="mb-3 leading-[1.65]">You agree not to:</p>
		<ul class="list-disc pl-6 leading-[1.65]">
			<li class="mb-2">
				cheat, automate drawings, or otherwise manipulate the AI scoring or the matchmaking;
			</li>
			<li class="mb-2">draw content that is illegal, hateful, harassing, or sexually explicit;</li>
			<li class="mb-2">disrupt the service, other players, or the underlying infrastructure;</li>
			<li class="mb-2">attempt to access accounts, data, or systems that are not yours.</li>
		</ul>
		<p class="mb-3 leading-[1.65]">
			Surrendering, disconnecting to dodge a loss, or abusing the reconnection grace period may be
			treated as a forfeit.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">4. Your content</h2>
		<p class="mb-3 leading-[1.65]">
			The drawings you create remain yours. By submitting them during a match, you grant us the
			limited right to process them in order to run the game (scoring, displaying, and matchmaking).
			We do not claim ownership of your drawings.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">5. Intellectual property</h2>
		<p class="mb-3 leading-[1.65]">
			The Draw Meter name, code, and visual design belong to the team that built it. You may not
			copy or redistribute the service as your own without permission.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">6. Availability</h2>
		<p class="mb-3 leading-[1.65]">
			The service is provided "as is" and "as available". As a student project, it may be offline,
			reset, or changed at any time without notice. Game state is held in memory and can be lost on
			a restart.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">7. Limitation of liability</h2>
		<p class="mb-3 leading-[1.65]">
			To the extent permitted by law, the team is not liable for any indirect or incidental damage
			arising from your use of the service, including loss of data or ranking.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">8. Termination</h2>
		<p class="mb-3 leading-[1.65]">
			We may suspend or remove accounts that break these terms. You may stop using the service and
			request deletion of your account at any time.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">9. Governing law</h2>
		<p class="mb-3 leading-[1.65]">
			These terms are governed by the laws of Switzerland, without regard to conflict-of-law rules.
		</p>
	</section>

	<section class="mb-8">
		<h2 class="mb-3 text-xl uppercase">10. Changes &amp; contact</h2>
		<p class="mb-3 leading-[1.65]">
			We may update these terms; continued use after a change means you accept the new version. For
			any question, reach the team through the project repository or your 42 Lausanne contact. See
			also our <a href="/privacy" class="font-semibold text-primary underline">Privacy Policy</a>.
		</p>
	</section>
</LegalPage>
