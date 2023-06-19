CREATE USER 'triplex'@'localhost' IDENTIFIED BY 'triplex';
GRANT ALL PRIVILEGES ON *.* TO 'triplex'@'localhost' WITH GRANT OPTION;
CREATE DATABASE IF NOT EXISTS triplex;
