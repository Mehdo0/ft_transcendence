<script lang="ts">
	// let data;
</script>

<body>
	<div class="center">
		<div class="square">
			<div class="center">
				<a href="/game/in-game"><button>Start game</button></a>
			</div>
			<div class="center">
				<a href="/game/lobby"><button>Join lobby</button></a>
			</div>
			<div class="center">
				<a href="/miscellaneous/ranking"><button>Ranking</button></a>
			</div>
			<div class="center">
				<a href="/miscellaneous/friends"><button>Friends</button></a>
			</div>
			<div class="center">
				<a href="/account/login"><button>Login</button></a>
			</div>
			<div class="center">
				<a href="/account/register"><button>Register</button></a>
			</div>
		</div>
	</div>
</body>

<style>
	body {
		background-color: lightblue;
	}
	.square {
		height: 425px;
		width: 400px;
		position: center;
		margin: 5%;
		border-radius: 10%;
		background-color: blueviolet;
	}
	button {
		border-color: aquamarine;
		align-items: center;
		font-size: large;
		height: 50px;
		width: 200px;
		margin: 5%;
		position: center;
		font-family: Verdana, Geneva, Tahoma, sans-serif;
	}
	.center {
		display: flex;
		justify-content: center;
		align-items: center;
	}
</style>
