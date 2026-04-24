"use client";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Table,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type Category = {
  id: string;
  name: string;
  description?: string | null;
  parent_id?: string | null;
};

export default function CategoriesPage() {
  const [items, setItems] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.listCategories();
      setItems(r as Category[]);
    } catch (e) {
      message.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onAdd() {
    try {
      const values = await form.validateFields();
      await api.createCategory(values);
      message.success("已创建");
      setOpen(false);
      form.resetFields();
      load();
    } catch (e) {
      if ((e as any)?.errorFields) return;
      message.error((e as Error).message);
    }
  }

  async function onDelete(id: string) {
    try {
      await api.deleteCategory(id);
      message.success("已删除");
      load();
    } catch (e) {
      message.error((e as Error).message);
    }
  }

  const columns: ColumnsType<Category> = [
    {
      title: "名称",
      dataIndex: "name",
      render: (n: string) => <Typography.Text strong>{n}</Typography.Text>,
    },
    { title: "描述", dataIndex: "description", ellipsis: true, render: (d) => d || "—" },
    {
      title: "操作",
      key: "ops",
      width: 100,
      render: (_: unknown, row) => (
        <Popconfirm
          title="确认删除该分类？"
          okButtonProps={{ danger: true }}
          onConfirm={() => onDelete(row.id)}
        >
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>分类管理</h1>
          <div className="subtitle">共 {items.length} 个分类</div>
        </div>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
          新建分类
        </Button>
      </div>

      <Card bordered={false}>
        <Table<Category>
          rowKey="id"
          dataSource={items}
          columns={columns}
          loading={loading}
          size="middle"
          pagination={false}
        />
      </Card>

      <Modal
        open={open}
        title="新建分类"
        onCancel={() => setOpen(false)}
        onOk={onAdd}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: "请输入分类名称" }]}
          >
            <Input placeholder="例如：文学、历史、编程" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="可选" />
          </Form.Item>
        </Form>
      </Modal>
    </AppShell>
  );
}
