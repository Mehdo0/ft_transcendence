This is a step by step guide on how to install better auth locally :

first you'll need to install the pkg using npm with this command:
```sh
npm install better-auth
```
once this is done you'll have to run this command to generate the env secret variable:
```sh
openssl rand -base64 32 
```

then update your .env file so it should look like this :

BETTER_AUTH_SECRET= {Insert the generated secret password here !}
BETTER_AUTH_URL=http://localhost:5173 #svelt url


