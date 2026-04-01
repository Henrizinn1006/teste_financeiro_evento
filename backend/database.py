import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import mysql.connector
from mysql.connector import Error as MySQLError

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "prototipofinanceiro")
DB_MODE = os.getenv("DB_MODE", "auto").lower()
SQLITE_PATH = Path(__file__).with_name("prototipofinanceiro.db")

_backend = None
_mysql_ready = False
_sqlite_ready = False


def _get_mysql_server_connection():
	return mysql.connector.connect(
		host=DB_HOST,
		port=DB_PORT,
		user=DB_USER,
		password=DB_PASSWORD,
		connection_timeout=5,
	)


def _get_mysql_database_connection():
	return mysql.connector.connect(
		host=DB_HOST,
		port=DB_PORT,
		user=DB_USER,
		password=DB_PASSWORD,
		database=DB_NAME,
		connection_timeout=5,
	)


def _initialize_mysql():
	global _mysql_ready

	if _mysql_ready:
		return

	conn = _get_mysql_server_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
		cursor.execute(f"USE `{DB_NAME}`")
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS eventos (
				id INT AUTO_INCREMENT PRIMARY KEY,
				nome VARCHAR(100)
			)
			"""
		)
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS movimentacoes (
				id INT AUTO_INCREMENT PRIMARY KEY,
				id_evento INT,
				tipo ENUM('entrada', 'saida'),
				valor DECIMAL(10,2),
				descricao VARCHAR(255),
				FOREIGN KEY (id_evento) REFERENCES eventos(id)
			)
			"""
		)
		cursor.execute("SELECT COUNT(*) FROM eventos")
		quantidade = cursor.fetchone()[0]
		if quantidade == 0:
			cursor.executemany(
				"INSERT INTO eventos (nome) VALUES (%s)",
				[("Evento 1",), ("Evento 2",), ("Evento 3",)],
			)
		conn.commit()
	finally:
		cursor.close()
		conn.close()

	_mysql_ready = True


def _get_sqlite_connection():
	conn = sqlite3.connect(SQLITE_PATH)
	conn.row_factory = sqlite3.Row
	conn.execute("PRAGMA foreign_keys = ON")
	return conn


def _initialize_sqlite():
	global _sqlite_ready

	if _sqlite_ready:
		return

	conn = _get_sqlite_connection()
	cursor = conn.cursor()

	try:
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS eventos (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				nome TEXT NOT NULL
			)
			"""
		)
		cursor.execute(
			"""
			CREATE TABLE IF NOT EXISTS movimentacoes (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				id_evento INTEGER NOT NULL,
				tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
				valor REAL NOT NULL,
				descricao TEXT NOT NULL,
				FOREIGN KEY (id_evento) REFERENCES eventos(id)
			)
			"""
		)
		cursor.execute("SELECT COUNT(*) FROM eventos")
		quantidade = cursor.fetchone()[0]
		if quantidade == 0:
			cursor.executemany(
				"INSERT INTO eventos (nome) VALUES (?)",
				[("Evento 1",), ("Evento 2",), ("Evento 3",)],
			)
		conn.commit()
	finally:
		cursor.close()
		conn.close()

	_sqlite_ready = True


def get_database_backend():
	global _backend

	if _backend is not None:
		return _backend

	if DB_MODE == "sqlite":
		_initialize_sqlite()
		_backend = "sqlite"
		return _backend

	if DB_MODE == "mysql":
		_initialize_mysql()
		_backend = "mysql"
		return _backend

	try:
		_initialize_mysql()
		_backend = "mysql"
	except MySQLError:
		_initialize_sqlite()
		_backend = "sqlite"

	return _backend


def initialize_database():
	return get_database_backend()


def listar_eventos_db():
	backend = get_database_backend()

	if backend == "mysql":
		conn = _get_mysql_database_connection()
		cursor = conn.cursor(dictionary=True)
		try:
			cursor.execute("SELECT id, nome FROM eventos ORDER BY id")
			return cursor.fetchall()
		finally:
			cursor.close()
			conn.close()

	conn = _get_sqlite_connection()
	cursor = conn.cursor()
	try:
		cursor.execute("SELECT id, nome FROM eventos ORDER BY id")
		return [dict(row) for row in cursor.fetchall()]
	finally:
		cursor.close()
		conn.close()


def obter_resumo_evento_db(id_evento):
	backend = get_database_backend()

	if backend == "mysql":
		conn = _get_mysql_database_connection()
		cursor = conn.cursor(dictionary=True)
		try:
			cursor.execute(
				"""
				SELECT tipo, SUM(valor) AS total
				FROM movimentacoes
				WHERE id_evento = %s
				GROUP BY tipo
				""",
				(id_evento,),
			)
			return cursor.fetchall()
		finally:
			cursor.close()
			conn.close()

	conn = _get_sqlite_connection()
	cursor = conn.cursor()
	try:
		cursor.execute(
			"""
			SELECT tipo, SUM(valor) AS total
			FROM movimentacoes
			WHERE id_evento = ?
			GROUP BY tipo
			""",
			(id_evento,),
		)
		return [dict(row) for row in cursor.fetchall()]
	finally:
		cursor.close()
		conn.close()


def listar_historico_evento_db(id_evento):
	backend = get_database_backend()

	if backend == "mysql":
		conn = _get_mysql_database_connection()
		cursor = conn.cursor(dictionary=True)
		try:
			cursor.execute(
				"""
				SELECT tipo, valor, descricao
				FROM movimentacoes
				WHERE id_evento = %s
				ORDER BY id DESC
				""",
				(id_evento,),
			)
			return cursor.fetchall()
		finally:
			cursor.close()
			conn.close()

	conn = _get_sqlite_connection()
	cursor = conn.cursor()
	try:
		cursor.execute(
			"""
			SELECT tipo, valor, descricao
			FROM movimentacoes
			WHERE id_evento = ?
			ORDER BY id DESC
			""",
			(id_evento,),
		)
		return [dict(row) for row in cursor.fetchall()]
	finally:
		cursor.close()
		conn.close()


def adicionar_movimentacao_db(id_evento, tipo, valor, descricao):
	backend = get_database_backend()

	if backend == "mysql":
		conn = _get_mysql_database_connection()
		cursor = conn.cursor()
		try:
			cursor.execute(
				"""
				INSERT INTO movimentacoes (id_evento, tipo, valor, descricao)
				VALUES (%s, %s, %s, %s)
				""",
				(id_evento, tipo, valor, descricao),
			)
			conn.commit()
		finally:
			cursor.close()
			conn.close()
		return

	conn = _get_sqlite_connection()
	cursor = conn.cursor()
	try:
		cursor.execute(
			"""
			INSERT INTO movimentacoes (id_evento, tipo, valor, descricao)
			VALUES (?, ?, ?, ?)
			""",
			(id_evento, tipo, valor, descricao),
		)
		conn.commit()
	finally:
		cursor.close()
		conn.close()
