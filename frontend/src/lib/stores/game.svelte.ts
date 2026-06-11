export const game = $state({
	id: '',
	opponent: '',
	players: [] as string[],
	me: '',
	word: '',
	my_score: 0,
	opponent_score: 0,
	scores: {} as Record<string, number>,
	is_ranked: true
});
