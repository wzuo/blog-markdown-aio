# asyncio aiohttp markdown blog

Used free template from StartBootstrap. Sources included in `static` directory.

## Technologies
Written in Python 3.5 in asynchronous way, using aiohttp framework. Posts are parsed from Markdown format. Comments are saved in TinyDB in `db.json` file.
Everything is dockerized, so Docker and Docker-Compose are required.

## Requirements
* docker-compose
* npm

## Running
Go into `static` directory and type in `npm install`. Then go to main directory and type in `docker-compose up -d`. That's all.

Site should be available on `localhost:8000`.

## Adding posts
Just create new file in `posts` directory. It requires a special format, as in example files:
* 1st line: title of post `# title`
* 2nd line: subtitle of post `## subtitle`
* 3rd line: date of post in format `YYYY-MM-DDTHH:MM:SS` `### 2017-04-05T14:45:00`
* 4th line: slug of post (visible in browser's address bar) `#### test-post`
* 5th line: author of post `##### John Doe`
* 6th line: special options of post. Currently possible option is only `disable_comments`, example: `###### disable_comments`. If no flags, then leave empty row, like that: `######`


## Removing comments
It has to be done manually in `db.json`

## License
MIT
