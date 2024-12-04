CREATE DATABASE IF NOT EXISTS rekomendasi_kegiatan;

USE rekomendasi_kegiatan;

CREATE TABLE IF NOT EXISTS kegiatan (
    NPM INT(7),
    TOTAL_HADIR INT(1),
    TOTAL_PERTEMUAN INT(1),
    TOTAL_TERLAKSANA INT(1),
    TOTAL_TIDAK_HADIR INT(1),
    NILAI VARCHAR(1),
    kategori_matakuliah VARCHAR(17),
    NAMA VARCHAR(28),
    IPK DECIMAL(3,2),
    NOMOR_PEMBIMBING INT(7),
    KEGIATAN VARCHAR(101),
    KATEGORI VARCHAR(17),
    kategori_matakuliah_encoded INT(2),
    KATEGORI_encoded INT(2),
    rating INT(1)
);
