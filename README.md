# Image Search

This repository contains the code of a simple image similarity search engine
built around the vector database [Weaviate](https://weaviate.io/).
Together with the index and search servers, users are able to index
zipped directories of images and search the created index for similar images.
Aside from the server code, the same functionality to index a folder of images
and search based on a reference image is also provided as a script in the
corresponding server directory.

## Installation

Before you get started, make sure you have
[Docker](https://www.docker.com/) and
[Docker Compose](https://docs.docker.com/compose/) installed.

To build the containers, from the project directory execute

```bash
docker-compose build .
```

If you wish to run the database without the additional helper servers,
for example if you wish to index via a script instead of the server,
run

```bash
docker-compose -f docker-compose.headless.yml build .
```

## Usage

To run the code, either headless or not, execute

```bash
docker-compose -f docker-compose.headless.yml up
```

or

```bash
docker-compose -f docker-compose.yml up
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
