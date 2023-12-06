DROP TABLE IF EXISTS `rooms`;
DROP TABLE IF EXISTS `messages`;
DROP TABLE IF EXISTS `members`;
CREATE TABLE `rooms` (
  `code` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`code`)
);

CREATE TABLE `messages` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `room_code` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `sender_name` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`room_code`) REFERENCES `rooms` (`code`) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE `members` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `room_code` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`room_code`) REFERENCES `rooms` (`code`) ON DELETE CASCADE ON UPDATE CASCADE
);