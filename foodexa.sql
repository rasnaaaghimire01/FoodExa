-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Sep 25, 2026 at 10:22 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `foodexa`
--

-- --------------------------------------------------------

--
-- Table structure for table `categories`
--

CREATE TABLE `categories` (
  `category_id` int(11) NOT NULL,
  `category_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `categories`
--

INSERT INTO `categories` (`category_id`, `category_name`) VALUES
(1, 'Momo'),
(2, 'Pizza'),
(3, 'Burger'),
(4, 'Drinks');

-- --------------------------------------------------------

--
-- Table structure for table `food_items`
--

CREATE TABLE `food_items` (
  `food_id` int(11) NOT NULL,
  `category_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `description` text DEFAULT NULL,
  `image` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `food_items`
--

INSERT INTO `food_items` (`food_id`, `category_id`, `name`, `price`, `description`, `image`) VALUES
(1, 1, 'Chicken Momo', 180.00, 'Steamed dumplings filled with minced chicken, served with tomato achar.', 'chicken_momo.jpg'),
(2, 1, 'Veg Momo', 140.00, 'Steamed dumplings filled with fresh cabbage, carrot and onion.', 'veg_momo.jpg'),
(3, 1, 'Jhol Momo', 200.00, 'Chicken momo served in a warm and spicy sesame soup.', 'jhol_momo.jpg'),
(4, 2, 'Margherita Pizza', 450.00, 'Classic pizza with tomato sauce, mozzarella cheese and basil.', 'margherita_pizza.jpg'),
(5, 2, 'Chicken Pizza', 550.00, 'Pizza topped with grilled chicken, onion, capsicum and cheese.', 'chicken_pizza.jpg'),
(6, 2, 'Veg Pizza', 480.00, 'Pizza topped with mushroom, sweet corn, capsicum and olives.', 'veg_pizza.jpg'),
(7, 3, 'Chicken Burger', 320.00, 'Crispy fried chicken patty with lettuce and mayonnaise.', 'chicken_burger.jpg'),
(8, 3, 'Veg Burger', 250.00, 'Vegetable patty with lettuce, tomato and special sauce.', 'veg_burger.jpg'),
(9, 3, 'Cheese Burger', 350.00, 'Chicken patty with a slice of melted cheese, onion and pickles.', 'cheese_burger.jpg'),
(10, 4, 'Coca Cola', 80.00, 'Chilled 250 ml bottle of Coca Cola.', 'coca_cola.jpg'),
(11, 4, 'Lassi', 120.00, 'Sweet and cold yogurt drink.', 'lassi.jpg'),
(12, 4, 'Masala Tea', 50.00, 'Hot milk tea made with ginger and spices.', 'masala_tea.jpg'),
(13, 1, 'Fried Momo', 190.00, 'Chicken momo fried until golden and crispy.', 'fried_momo.jpg'),
(14, 1, 'C Momo', 220.00, 'Fried chicken momo tossed in a hot and tangy chilli sauce.', 'c_momo.jpg'),
(15, 1, 'Kothey Momo', 200.00, 'Half steamed, half pan fried momo with a crispy bottom.', 'kothey_momo.jpg'),
(16, 2, 'Paneer Pizza', 520.00, 'Pizza topped with spiced paneer, onion and green capsicum.', 'paneer_pizza.jpg'),
(17, 2, 'BBQ Chicken Pizza', 600.00, 'Smoky barbecue chicken with onion and mozzarella cheese.', 'bbq_chicken_pizza.jpg'),
(18, 2, 'Mushroom Pizza', 470.00, 'Fresh mushroom, garlic and cheese on a thin crust.', 'mushroom_pizza.jpg'),
(19, 3, 'Double Chicken Burger', 450.00, 'Two chicken patties with cheese, lettuce and our house sauce.', 'double_chicken_burger.jpg'),
(20, 3, 'Paneer Burger', 300.00, 'Grilled paneer slice with onion, tomato and mint mayo.', 'paneer_burger.jpg'),
(21, 3, 'Buff Burger', 340.00, 'Juicy buff patty with caramelised onion and cheese.', 'buff_burger.jpg'),
(22, 4, 'Cold Coffee', 160.00, 'Chilled coffee blended with milk and ice cream.', 'cold_coffee.jpg'),
(23, 4, 'Fresh Lime Soda', 100.00, 'Fresh lime juice with soda, served sweet or salted.', 'fresh_lime_soda.jpg'),
(24, 4, 'Mango Lassi', 150.00, 'Thick and cold yogurt drink made with ripe mango.', 'mango_lassi.jpg');

-- --------------------------------------------------------

--
-- Table structure for table `orders`
--

CREATE TABLE `orders` (
  `order_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `order_date` datetime NOT NULL DEFAULT current_timestamp(),
  `total_amount` decimal(10,2) NOT NULL,
  `status` enum('Pending','Preparing','Ready to Deliver','Delivered','Cancelled') NOT NULL DEFAULT 'Pending'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `order_items`
--

CREATE TABLE `order_items` (
  `item_id` int(11) NOT NULL,
  `order_id` int(11) NOT NULL,
  `food_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `price` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `role` enum('customer','admin') NOT NULL DEFAULT 'customer'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `name`, `email`, `password`, `phone`, `role`) VALUES
(1, 'Rasna Ghimire', 'rasnaghimire@gmail.com', 'scrypt:32768:8:1$DG18BjblIvvDrWK9$1005532b4408a340421d0c2ac5bf3fade338a47b5901b0ffcbb16c308e7545e2ffa4139fb9fa41606a558cb14afda974bbe2c7946b5f89231721f95cf960788a', NULL, 'admin'),
(2, 'Rasna', 'rasna5@gmail.com', 'scrypt:32768:8:1$oM0joYaocpQcWkFX$8d2fb8df39272421247c0ae4975d043ca9a9d47d22a6f9f85b219a3a1519e667e36081dd452d7717735b185d3552cf6f2ee92d9aeaca691048e64d74cd7643ad', '9845087545', 'customer'),
(3, 'Shrijana', 'shrijana1@gmail.com', 'scrypt:32768:8:1$fTJOzK2mSUWoPAp3$34c78cd59c83808334dda8c4e06d5e3d31950e8d72d9de1d6cdb100a8d287a4dfb96e3344dfe192efcd80e20529abe16bf49f48fbe9fbe61d6d474751d9b199d', '9845216581', 'customer'),
(4, 'Soni', 'soni2@gmail.com', 'scrypt:32768:8:1$eA41X5o6QkCYCB4T$98553ce8b1c556b310aa387dfacc9e6bbbc17eb6b0a6229ddf0129cec72a9e9259ded916deb2c5894f870497bab81f54f46f901bbbec2869a5c06e539d4b178c', '9861452307', 'customer'),
(5, 'Bipana', 'bipana3@gmail.com', 'scrypt:32768:8:1$gnj6AeSzRsf3tttd$a711676f6fb036ebaf220176cdeab1196fc3c9b9105a174e4565fef6d17ee720e8da97553c4b9be3a10740fa5939a9a26479ee98a3a7f0b579b8dbac931a4b22', '9807654321', 'customer'),
(6, 'Asmita', 'asmita4@gmail.com', 'scrypt:32768:8:1$wQVXjNPR2DLJBo5v$b779a7ea55e2f5ac097dfee3bbfcd965edca53482bddfd78725273b3da862ca58d409532d0f09d3a00f55b1ab5e174d018aec81c42ffa9995611612692132531', '9812456789', 'customer');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `categories`
--
ALTER TABLE `categories`
  ADD PRIMARY KEY (`category_id`);

--
-- Indexes for table `food_items`
--
ALTER TABLE `food_items`
  ADD PRIMARY KEY (`food_id`),
  ADD KEY `category_id` (`category_id`);

--
-- Indexes for table `orders`
--
ALTER TABLE `orders`
  ADD PRIMARY KEY (`order_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `order_items`
--
ALTER TABLE `order_items`
  ADD PRIMARY KEY (`item_id`),
  ADD KEY `order_id` (`order_id`),
  ADD KEY `food_id` (`food_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `categories`
--
ALTER TABLE `categories`
  MODIFY `category_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `food_items`
--
ALTER TABLE `food_items`
  MODIFY `food_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

--
-- AUTO_INCREMENT for table `orders`
--
ALTER TABLE `orders`
  MODIFY `order_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `order_items`
--
ALTER TABLE `order_items`
  MODIFY `item_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `food_items`
--
ALTER TABLE `food_items`
  ADD CONSTRAINT `food_items_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`);

--
-- Constraints for table `orders`
--
ALTER TABLE `orders`
  ADD CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `order_items`
--
ALTER TABLE `order_items`
  ADD CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`),
  ADD CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`food_id`) REFERENCES `food_items` (`food_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
