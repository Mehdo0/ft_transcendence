export const game = $state({
	id: '',
	opponents: [] as string[],
	players: [] as string[],
	me: '',
	word: '',
	scores: {} as Record<string, number>,
	is_ranked: true
});
