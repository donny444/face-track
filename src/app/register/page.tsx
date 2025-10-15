"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";

import "bootstrap/dist/css/bootstrap.min.css";
import { Container, Row, Col, Form, Button, Alert } from "react-bootstrap";

import { useSelector } from "react-redux";
import { RootState } from "../contexts/store";

import { ThemeEnum } from "@/interfaces/enums";
import axios from "axios";

export default function RegisterPage() {
  const router = useRouter();
  const theme = useSelector((state: RootState) => state.theme.mode);
  const [formData, setFormData] = useState({
    email: "",
    firstName: "",
    lastName: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string>('')
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // เช็คนามสกุลไฟล์
      const fileType = file.type
      if (!fileType.includes('jpeg') && !fileType.includes('jpg') && !fileType.includes('png')) {
        setError('กรุณาอัพโหลดไฟล์ .jpg หรือ .png เท่านั้น')
        return
      }
      
      // สร้าง preview
      const reader = new FileReader()
      reader.onloadend = () => {
        setImagePreview(reader.result as string)
      }
      reader.readAsDataURL(file)
      
      setImageFile(file)
      setError('')
    }
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      const formDataWithImage = new FormData()
      formDataWithImage.append('email', formData.email)
      formDataWithImage.append('first_name', formData.firstName)
      formDataWithImage.append('last_name', formData.lastName)
      formDataWithImage.append('password', formData.password)
      if (imageFile) {
        formDataWithImage.append('image', imageFile)
      }

      const response = await axios.post("http://localhost:8000/register", 
        formDataWithImage,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
      );

        if (response.status === 200) {
          console.log("Register success");
          alert("Register success");
          router.push("/login");
        }
      } catch (error) {
        console.error(error);
        if (axios.isAxiosError(error) && error.response) {
          // ถ้ามี error response จาก server
          setError(error.response.data.error || "Registration failed");
        } else {
          // ถ้าเป็น error อื่นๆ
          setError("Registration failed. Please try again.");
        }
      }
    }

  return (
    <Container
      fluid
      className={`min-vh-100 ${
        theme === ThemeEnum.DARK ? "bg-dark" : "bg-light"
      } d-flex align-items-center justify-content-center`}
    >
      <Row className="w-100 justify-content-center">
        <Col md={6} lg={4}>
          <div
            className={`${
              theme === ThemeEnum.DARK ? "bg-dark text-white" : "bg-white"
            } p-4 rounded-lg shadow-sm`}
          >
            <h2
              className={`text-center ${
                theme === ThemeEnum.DARK ? "text-white" : "text-primary"
              } mb-4`}
            >
              สมัครสมาชิก
            </h2>

            {error && (
              <Alert variant="danger" className="mb-3">
                {error}
              </Alert>
            )}

            <Form onSubmit={handleSubmit}>
              <Form.Group className="mb-3">
                <Form.Label
                  className={
                    theme === ThemeEnum.DARK ? "text-white" : "text-black"
                  }
                >
                  อีเมล
                </Form.Label>
                <Form.Control
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="กรอกอีเมลของคุณ"
                  required
                  className={`form-control-lg ${
                    theme === ThemeEnum.DARK ? "bg-dark text-white" : ""
                  }`}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label
                  className={
                    theme === ThemeEnum.DARK ? "text-white" : "text-black"
                  }
                >
                  ชื่อ
                </Form.Label>
                <Form.Control
                  type="text"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleChange}
                  placeholder="กรอกชื่อของคุณ"
                  required
                  className={`form-control-lg ${
                    theme === ThemeEnum.DARK ? "bg-dark text-white" : ""
                  }`}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label
                  className={
                    theme === ThemeEnum.DARK ? "text-white" : "text-black"
                  }
                >
                  นามสกุล
                </Form.Label>
                <Form.Control
                  type="text"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleChange}
                  placeholder="กรอกนามสกุลของคุณ"
                  required
                  className={`form-control-lg ${
                    theme === ThemeEnum.DARK ? "bg-dark text-white" : ""
                  }`}
                />
              </Form.Group>

              <Form.Group className="mb-4">
                <Form.Label
                  className={
                    theme === ThemeEnum.DARK ? "text-white" : "text-black"
                  }
                >
                  รหัสผ่าน
                </Form.Label>
                <Form.Control
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="กรอกรหัสผ่าน"
                  required
                  className={`form-control-lg ${
                    theme === ThemeEnum.DARK ? "bg-dark text-white" : ""
                  }`}
                />
              </Form.Group>

              <Form.Group className="mb-4">
                <Form.Label className={theme === ThemeEnum.DARK ? 'text-white' : 'text-black'}>
                  กรุณาอัพโหลดไฟล์รูปภาพ
                </Form.Label>
                <div className={`small mb-2 ${theme === ThemeEnum.DARK ? 'text-light' : 'text-muted'}`}>
                  รองรับไฟล์ .jpg และ .png เท่านั้น
                </div>
                <Form.Control
                  type="file"
                  accept=".jpg,.jpeg,.png"
                  onChange={handleImageChange}
                  className={`form-control-lg ${theme === ThemeEnum.DARK ? 'bg-dark text-white' : ''}`}
                />
                {imagePreview && (
                  <div className="mt-2 text-center">
                    <Image 
                      src={imagePreview}
                      alt="Preview"
                      width={200}
                      height={200}
                      style={{ 
                        borderRadius: '8px',
                        objectFit: 'contain'
                      }}
                    />
                  </div>
                )}
              </Form.Group>

              <Form.Group className="mb-4">
                <Form.Label className={theme === ThemeEnum.DARK ? 'text-white' : 'text-black'}>
                  กรุณาอัพโหลดไฟล์รูปภาพ
                </Form.Label>
                <div className={`small mb-2 ${theme === ThemeEnum.DARK ? 'text-light' : 'text-muted'}`}>
                  รองรับไฟล์ .jpg และ .png เท่านั้น
                </div>
                <Form.Control
                  type="file"
                  accept=".jpg,.jpeg,.png"
                  onChange={handleImageChange}
                  className={`form-control-lg ${theme === ThemeEnum.DARK ? 'bg-dark text-white' : ''}`}
                />
                {imagePreview && (
                  <div className="mt-2 text-center">
                    <Image 
                      src={imagePreview}
                      alt="Preview"
                      width={200}
                      height={200}
                      style={{ 
                        borderRadius: '8px',
                        objectFit: 'contain'
                      }}
                    />
                  </div>
                )}
              </Form.Group>

              <Button
                variant={theme === ThemeEnum.DARK ? "light" : "primary"}
                type="submit"
                className="w-100 mb-3 py-2"
                size="lg"
              >
                สมัครสมาชิก
              </Button>
            </Form>
          </div>
        </Col>
      </Row>
    </Container>
  );
}
