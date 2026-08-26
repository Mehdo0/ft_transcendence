import type { RoundResult } from '$lib/game/roundResult';

type Scores = Record<string, number>;

export type MatchFoundMessage = {
	type: 'match_found';
	game_id: string;
	opponent: string[];
	players: string[];
	me: string;
	word: string;
	duration: number;
	countdown: number;
	scores: Scores;
	round_wins: Scores;
	round_number: number;
	is_ranked: boolean;
};

type ReconnectGameMessage = {
	type: 'reconnect_game';
	game_id: string;
	opponent: string[];
	players: string[];
	me: string;
	word: string;
	time_left: number;
	duration: number;
	countdown: number;
	countdown_left: number;
	scores: Scores;
	round_wins: Scores;
	round_number: number;
	round_result: RoundResult | null;
	is_ranked: boolean;
};

type GameInfoMessage =
	| { type: 'game_info'; exist: false }
	| {
			type: 'game_info';
			exist: true;
			game_id: string;
			opponent: string[];
			players: string[];
			me: string;
			word: string;
			time_left: number;
			duration: number;
			countdown: number;
			countdown_left: number;
			scores: Scores;
			round_wins: Scores;
			round_number: number;
			round_result: RoundResult | null;
			is_ranked: boolean;
	  };

type LobbyInfoMessage =
	| { type: 'lobby_info'; exist: false }
	| {
			type: 'lobby_info';
			exist: true;
			players: string[];
			host: string;
			me: string;
	  };

type RoundResultMessage = RoundResult & { type: 'round_result' };

export type ServerMessage =
	| { type: 'connection_ready' }
	| { type: 'connection_replaced' }
	| { type: 'error'; message: string }
	| { type: 'waiting' }
	| { type: 'matchmaking_cancelled' }
	| { type: 'lobby_created'; code: string }
	| { type: 'lobby_joined'; code: string }
	| LobbyInfoMessage
	| { type: 'player_joined'; username: string }
	| { type: 'player_left'; username: string }
	| { type: 'lobby_closed' }
	| MatchFoundMessage
	| { type: 'ai_guess'; username: string; guess: Scores; scores: number }
	| { type: 'player_guess'; username: string; guess?: Scores; score: number }
	| { type: 'opponent_disconnected'; username: string }
	| { type: 'opponent_reconnected'; username: string }
	| { type: 'opponent_surrendered' }
	| ReconnectGameMessage
	| RoundResultMessage
	| {
			type: 'next_round';
			word: string;
			duration: number;
			countdown: number;
			scores: Scores;
			round_wins: Scores;
			round_number: number;
	  }
	| {
			type: 'end_game';
			status: 'winner' | 'loser' | 'looser' | 'draw';
			elo_diff: number;
			new_elo: number;
			reason?: string;
	  }
	| GameInfoMessage;

export function parseServerMessage(value: unknown): ServerMessage | null {
	if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
	const message = value as Record<string, unknown>;
	if (typeof message.type !== 'string') return null;
	return message as ServerMessage;
}
