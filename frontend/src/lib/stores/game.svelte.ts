export const game = $state({
	id: '',
	opponents: [] as string[],
	players: [] as string[],
	me: '',
	word: '',
	scores: {} as Record<string, number>,
	round_number: 1,
	is_ranked: true
});
