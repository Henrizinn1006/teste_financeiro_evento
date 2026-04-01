CREATE DATABASE prototipofinanceiro;
USE prototipofinanceiro;

CREATE TABLE eventos (
	id INT AUTO_INCREMENT PRIMARY KEY,
	nome VARCHAR(100)
);

CREATE TABLE movimentacoes (
	id INT AUTO_INCREMENT PRIMARY KEY,
	id_evento INT,
	tipo ENUM('entrada', 'saida'),
	valor DECIMAL(10,2),
	descricao VARCHAR(255),
	FOREIGN KEY (id_evento) REFERENCES eventos(id)
);

INSERT INTO eventos (nome) VALUES
('Evento 1'),
('Evento 2'),
('Evento 3');