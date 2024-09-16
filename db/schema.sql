CREATE DATABASE IF NOT EXISTS `db_filmlandia`;

USE `db_filmlandia`;

CREATE TABLE IF NOT EXISTS tb_usuarios (
    usu_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    usu_nome VARCHAR(100) NOT NULL,
    usu_senha VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS tb_filmes (
    fil_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    fil_nome VARCHAR(100) NOT NULL,
    fil_genero VARCHAR(100) NOT NULL,
    fil_usu_id INT NOT NULL,
    FOREIGN KEY (fil_usu_id) REFERENCES tb_usuarios(usu_id)
);

CREATE TABLE IF NOT EXISTS tb_avaliacoes (
    ava_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    ava_nota INT NOT NULL,
    ava_comentario TEXT NOT NULL,
    ava_fil_id INT NOT NULL,
    FOREIGN KEY (ava_fil_id) REFERENCES tb_filmes(fil_id),
    ava_usu_id INT NOT NULL,
    FOREIGN KEY (ava_usu_id) REFERENCES tb_usuarios(usu_id)
);
