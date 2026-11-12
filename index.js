let cars = [
  { name: "BMW", price: 20000, comfort: true },
  { name: "Audi", price: 50000, comfort: false },
];

cars.forEach((car) => {
  if (car.price >= 1000 && car.comfort === false) {
    console.log(`${car.name} qimmat va komfort`);
  } else {
    console.log(`${car.name}  arzon va noqulay moshin`);
  }
});
